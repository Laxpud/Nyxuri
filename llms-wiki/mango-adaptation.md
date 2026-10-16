# Mango WM 适配契约 (Mango WM Adaptation)

> 本页是 Nyxuri 对 Mango (mangowm / wlroots) 合成器适配的架构契约与设计决策记录，以源码（`configs/mango/` 与 `nyxuri/`）为准。

## 1. 架构总览与双轴定位

Mango (`mangowm`) 是一款现代、轻量、基于 wlroots 的 Wayland 合成器，具备类似 Niri 的 Scroller（无限滚动）与 Dwm-like 平铺混合模式。

遵循 Nyxuri 的 [two-axis-config](two-axis-config.md)（双轴解耦）设计：
- **配置轴（Axis A）**：`configs/mango/` 目录存在，由部署引擎原子复制到 `~/.config/mango/`。
- **可选轴（Axis B）**：在 `configs/mango/manifest.toml` 声明 `optional = true`，为可选桌面组件（`packages = ["mangowm"]`），不强占系统硬依赖，不破坏 PKGBUILD 纯度。

## 2. 目录结构与配置文件分工

```
configs/mango/
├── manifest.toml       # 单元清单（preserve、chmod、reload 钩子、optional）
├── config.conf         # 核心合成器配置
├── monitors.conf       # 显示器配置（由 Noctalia 生成，动态保留）
├── __custom__.conf     # 用户自定义配置（Dunder 保护）
└── scripts/
    ├── session-shell.sh    # 外壳启动网关（nyxuri-shell / noctalia 探测与回退）
    ├── shell-action.sh     # 桌面外壳动作网关（启动器、锁屏、壁纸、翻译等）
    ├── mango-brightness.sh # 亮度调节脚本（内屏背光 + 外接屏 DDC/CI 穿透）
    └── hotkey-helper.py    # 按键引导与速查器（Mod+/ 触发，动态解析 config.conf）
```

## 3. 核心设计契约与不变量

### 3.1 Dunder 与 Preserve 双机制保障
- **`monitors.conf` 与 `noctalia.conf`**：在 `configs/mango/manifest.toml` 中声明为 `preserve`，更新与部署时不覆盖运行时状态。
- **`__custom__.conf`**：命名遵循 Dunder 协议，由部署引擎 `atomic_replace_item` 自动继承，用户在其中添加的自定义按键与窗口规则永久生效。
- **优雅包含**：在 `config.conf` 中统一使用 `source_optional=` 语法（如 `source_optional=~/.config/mango/noctalia.conf`），即使外部文件尚未生成也不会导致合成器报错或中断。

### 3.2 外壳与脚本解耦
- **外壳网关**：快捷键不硬编码特定桌面外壳命令，通过 `/home/user/.config/mango/scripts/shell-action.sh` 统一分发至当前活动的桌面外壳（Noctalia 或 Nyxuri 自研 Shell），支持 Orbit 星环启动器、划词翻译与壁纸选择器。
- **会话启动**：通过 `session-shell.sh` 挂载桌面外壳，并自动清理残留 scope。
- **按键速查**：通过 `hotkey-helper.py` 解析当前合成器配置并经由 Rofi 提供全局快捷键可视化检索面板。
- **路径中立**：脚本引用统一采用 `/home/user` 模板占位符，由 `nyxuri.deploy.templates` 部署时自动重写为目标 `$HOME`。

### 3.3 主题同步与渲染管线
- **Noctalia 模板注册**：`configs/noctalia/noctalia-config.toml` 在 `[theme.templates.user.nyxuri_mango]` 中挂载 `configs/noctalia/templates/mango.conf`（适配 MangoWM >= 0.18.0 的 `snake_case` 颜色键名与 0.18.1 Auto Tab Bar 配色）。Noctalia 取色引擎会自动将配色渲染至 `~/.config/mango/noctalia.conf`。
- **GTK 与 Qt 平台统一**：MangoWM 会话环境变量声明 `QT_QPA_PLATFORMTHEME=gtk3`，结合 `qt5-wayland` / `qt6-wayland` 与 `libqgtk3.so`，使 Qt5/Qt6 应用全面无感继承 GTK3 的 Material You 调色板、图标主题与字体。
- **全局光标一致性**：显式配置 `cursor_theme=Colloid-dark-cursors` 及 `XCURSOR_THEME` / `XCURSOR_SIZE` 环境变量，与 GTK、Qt 及 XWayland 保持零割裂。
- **热重载总线**：在 `nyxuri/theme.py` 主题同步与切换时，自动探测并执行 `mmsg dispatch reload_config`，实现免重启即时变色。

### 3.4 门户路由 (XDG Desktop Portal)
- 在 `configs/xdg-desktop-portal/mango-portals.conf` 中为 Mango 单独配置 `preferred` 路由：
  - `ScreenCast` 与 `Screenshot` 显式路由至 `wlr`（由 `xdg-desktop-portal-wlr` 处理 `zwlr-screencopy` 协议），规避 GNOME/Mutter 专属后端的启动崩溃。

## 4. 验证方式

```bash
# 1. 语法检查
mango -c configs/mango/config.conf -p

# 2. 契约单测
python3 -m unittest tests/test_mango_adaptation.py

# 3. 全局单测与文档闭包验证
python3 -m unittest discover -s tests -q
```

## 5. 过渡债务与收编路线 (Transitional Debt)

> 按 ROADMAP「退役清单制」登记：下列引擎特判是多合成器适配的**过渡形态**。
> 第三个合成器（Hyprland/Sway）接入前必须收编，禁止再往元组里加第三个字面量。

| 过渡物 | 位置 | 收编阶段 |
| --- | --- | --- |
| `SUPPORTED_WMS` 硬编码元组 + `detect_preferred_wm()` | `nyxuri/constants.py` | KM1 `UnitRegistry`（合成器类别改由单元 manifest 声明） |
| 组件菜单 WM/应用分部与 radio 单选 | `nyxuri/menus.py`、`nyxuri/tui.py` | KM3 TUI 工坊（4 动词接管后重审） |
| doctor 三处 `("mango", "niri")` 字面量 | `nyxuri/doctor.py` | Shell 后生态 `CompositorDriver` 驱动抽象层 |
| greeter 会话参数 WM 特判 | `nyxuri/modules/greeter.py` | 同上（`greeter` 会话自适应） |

不属于债务的部分：`configs/mango/` 整目录（单元形态，KM1 后原样存活）、
`nyxuri/theme.py` 的 `mmsg` 探针（与既有 `pkill`/`kitty` 探针同模式）、
`nyxuri/deploy/templates.py` 的 `/home/user` 占位符渲染（不变量 5 的既有实现）。
