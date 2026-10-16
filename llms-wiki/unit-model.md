# Unit Model — 单元模型、内核架构与极简契约

> 本页是 Nyxuri 单元模型、内核架构、状态机与 Manifest Schema v2 的唯一权威契约；
> 运行时行为与单测以 `tests/test_unit_model.py` 为准。

---

## 1. 物理空间三对偶与不变量

系统由三个物理隔离的空间与一条单向中轴连接，互不侵犯：

```
┌────────────────────────────────┐
│   空间 A：源码蓝图 (Blueprint)  │  只读，版本受控，平铺所有单元目录
│   路径：configs/<unit>/         │  （永不向此处写入运行时状态）
└───────────────┬────────────────┘
                │
                │  中轴：nyxuri.deploy.atomic
                │  （哈希比对、原子替换、模板渲染、Dunder/Preserve 继承）
                ▼
┌────────────────────────────────┐       停用归档 (Vault In)       ┌─────────────────────────────────┐
│   空间 B：实机生活区 (Living)   │ ──────────────────────────────► │   空间 C：状态与保险域 (State)   │
│   路径：~/.config/<target>/    │ ◄────────────────────────────── │   路径：~/.local/state/nyxuri/  │
│   （用户的日常桌面生活环境）    │       启用恢复 (Vault Out)      │   - state.json (单一真相账本)    │
└────────────────────────────────┘                                 │   - vault/<unit>/ (自定义备份)  │
                                                                   │   - backups/ (30 个滚动快照)    │
                                                                   └─────────────────────────────────┘
```

### 空间不变量
1. **源码绝对只读**：`configs/` 永远是只读蓝图。严禁在源码树建软链接，严禁向源码树写状态。
2. **实机白纸洁癖**：未启用的单元在实机 `~/.config/<target>` 必须 100% 抹净，不留任何受管文件或幽灵残留。
3. **心血零丢失**：单元停用时，用户的自定义文件（`__custom__` 与 `preserve`）原样存入空间 C 的 `vault/<unit>/`；实机还原纯白，心血在保险库有据可查。

---

## 2. 四大法定术语 (The 4 Canonical Primitives)

全库统一且仅承认以下四个词：

| 术语 | 英文 | 本质定义 | 物理承载 | 行为边界 |
|---|---|---|---|---|
| **单元** | `Unit` | 桌面上**一切可独立开关**的原子能力实体。 | `configs/<unit>/` 目录 | 拥有独立的生命周期与状态，可声明依赖、文件与预设。 |
| **内核** | `Kernel` | Nyxuri 常驻骨架，负责编排与记账（纯 Python 标库）。 | `nyxuri/{registry, resolver, transaction, ledger}` | **内核不是单元**，不可插件化、不可开关，是承载一切的物理底座。 |
| **源** | `Source` | 单元的供给方与索引来源。 | 本地抽象 `local:builtin`（对应 `configs/`） | 本阶段仅维持单一本地内置源，推迟网络多源。 |
| **manifest** | `Manifest` | 单元的自描述规格书。全库统称 `manifest.toml`。 | `configs/<unit>/manifest.toml` | 纯声明式静态元数据，**全字段可选，无文件 = 全默认**。 |

### 严正排除项
* **系统软件包（pacman / AUR / Flatpak 包）**：不是单元！它们只是单元声明书里写的 `dependencies`。
* **预设与零件（Preset / Parts）**：不是单元！它们是单元内部的配置变体（Variants）。

---

## 3. 正交模型与状态机 (Orthogonal State Machine)

单元与预设各管各的，两轴严格垂直正交：
* **开关状态（横轴，存在性）**：用不用该软件？（`enabled` ↔ `disabled`）
* **外观形态（纵轴，呈现参数）**：软件长什么样？（`preset` / `parts`）

```
                [ Disabled ] (停用态：实机无文件，自定义配置存 Vault)
                     │
           on / enable       off / disable
         (预检清单与安装)   (归档抹净还原白纸)
                     ▼
                [ Enabled ]  (启用态：实机存在配置，服务活跃)
                     │
                     └── 内部形态切换：preset / parts（不改变 Enabled 状态）
```

### 迁移事务规则
1. **启用动作 (`on` / `enable`)**：
   - 依赖解析器遍历依赖链：若下游依赖未启用，一同列入启用预检清单；
   - 检查外部包：若缺少 pacman/AUR 包，调用 `nyxuri.pkg` 提示安装；
   - 从 `vault/<unit>/` 捞回自定义文件与最新蓝图合并；
   - 原子置换进 `~/.config/<target>` 并完成模板渲染；
   - 状态写入 `state.json`，通过轻量 IPC 信号通知 Shell 刷新。
2. **停用动作 (`off` / `disable`)**：
   - 反向依赖检查：若有其他已启用单元依赖它且未带 `--cascade`，强行阻断并报警；
   - 将 `~/.config/<target>` 中的 `__custom__` 与 `preserve` 文件原子移入 `vault/<unit>/`；
   - 彻底删除受管文件，空目录删除，实机恢复纯白；
   - 状态写入 `state.json`；
   - 真诚报告交底：明确告知配置已归档，二进制包保留在系统（不背着用户 sudo 卸包）；
   - 通过 IPC 信号通知 Shell 移除对应挂件。

---

## 4. Manifest Schema v2 极简规范

坚持**约定优于配置（Zero-Config by Default）**：
* 单元名称 = 目录名；
* 部署目标 = `~/.config/<目录名>`（除非显式指定 `target`）；
* 系统包名 = `[<目录名>]`（除非显式指定 `packages`）；
* **无 `manifest.toml` = 100% 采用全默认**（如 `kitty/` 目录不需要任何 TOML 文件）。

### 差异化字段范式（只写例外）

```toml
# 目标路径例外（如单文件目标）
target = "starship.toml"

# 系统包名例外（如带连字符或特殊命名）
packages = ["mission-center"]
packages_aur = ["brave-bin"]
packages_flatpak = ["com.qq.QQ"]

# 依赖的其他 Nyxuri 单元
dependencies = []

# 跨部署保留文件与可执行脚本权限
preserve = ["monitor.kdl"]
chmod = ["scripts/*.sh"]

# 预设与重载命令
[presets]
default = "default"
reload = ["niri", "msg", "action", "reload-config"]

# 通用零件插槽
[parts.effects]
target = "effects_normal.kdl"
source_dir = "effects"
default = "default"

# 特权声明（涉及 /etc 修改）
[privilege]
requires_root = false
system_paths = []
```

---

## 5. 四大核心命令

命令行只保留 4 个通用动词（`list`、`on`、`off`、`doctor`），支持直觉短动词别名：

```bash
# 1. 查看全景清单或单个详情
nyxuri list [unit]              # 别名: ls

# 2. 开启单元（支持指定预设）
nyxuri on <unit> [--preset <p>] # 别名: enable

# 3. 关闭单元（级联关闭下游依赖）
nyxuri off <unit> [--cascade]   # 别名: disable

# 4. 对账检查（实机文件 vs 账本三态审计）
nyxuri doctor [unit]            # 别名: doc
```

---

## 6. Shell 内部完全单元化与协同契约 (Shell Unitization & Coordination)

> **设计初衷**：当前 Shell 超过 50% 组件为借用的临时过渡品，未来将由作者大幅重构与推倒重写。微内核 + 几何插槽保证了借用组件与外壳的**绝对绝缘**——拔除、重写或替换任意组件，微内核与其他模块零改动。

Nyxuri Shell 绝非特权单体，其内部亦彻底单元化。Shell 本身蜕变为极致精简的**微内核宿主（Micro-Kernel Host）**，仅保留动作网关（`ActionGateway`）、会话协议（`NiriService`）、主题代币（`ThemeTokens`）与插槽宿主（`SlotHost`），其内部功能域全部升格为平等的 Shell 单元。

### 1. 六大几何插槽模型 (The 6 Geometric Slots)
所有 Shell 单元（`shell/units/<domain>/`）向唯一的 6 种几何插槽声明挂载点：
* **`edge:<top|bottom|left|right>`**（屏幕边缘）：如 `bar`、`dock`（独占边距排除区）；
* **`island`**（动态中枢）：如 `keystone` 顶部浮岛，微动展开收拢；
* **`overlay`**（全屏模态）：如 `lock`、`session`、`regionselector`；
* **`drawer:<left|right>`**（抽屉侧边）：如 `sidebars` 仪表盘；
* **`surface:desktop`**（底层画布）：如 `desktopcards` 桌面卡片、`wallpaper`；
* **`popup:notification`**（通知气泡）：如 `notifications` 弹窗宿主。

### 2. 动态装载与零内存释放闭包
* 微内核 `AppShell.qml` 内部消灭所有硬编码组件，仅保留数据驱动的 `Repeater` 与 `Loader`；
* 单元处于 `disabled` 时，`Loader.active = false`；实例当场销毁，其 Process、Timer、Socket 与回调全部注销；**冷启动时未启用功能域零读文件、零加载、内存占用为 0**。

### 3. 横向解耦与单一开关真相
* **横向零依赖**：Shell 单元之间严禁跨域调用，跨域桌面意图唯一路由至 `ActionGateway.executeIntent()`；
* **双向单一真相**：Shell 设置面板拨动开关仅通过 `ActionGateway` 派发 `nyxuri on/off` 调用内核事务，Shell 永远只是账本在屏幕上的**只读投影**；
* **单向 IPC 刷新**：内核事务落账后仅执行 `quickshell ipc unit reload`，Shell 热拉取账本重绘，零闪烁、不重启进程；
* **统一命名空间**：Shell 单元一律以 `shell.<domain>` 统一挂入 `state.json` 与 4 大动词管辖（如 `nyxuri off shell.dock`）。

---

## 7. 深层防御与代码级死刑清单

1. **包管理非对称**：`disable` 只撤回配置与桌面集成，绝不私自调用 sudo 卸载系统包，以避免打断和破坏系统依赖；结果在执行报告中如实写明。
2. **单文件特例一律铲除**：全库 100% 目录平铺化。`configs/starship.toml` 升格为 `configs/starship/`，消灭 sidecar 机制。
3. **Vault 纯文件平铺**：`~/.local/state/nyxuri/vault/<unit>/` 保持目录镜像平铺，不建数据库，不打包压缩，用户肉眼直观可见。
4. **代码级死刑断言**：在契约测试 `tests/test_ai_specs.py` 中写死断言：
   - 到达 **KM1** 时，`.optional-apps.toml` 与 `starship.toml` 必须物理删除；
   - 到达 **KM5** 时，`nyxuri/cli.py` 内部所有硬编码的专用命令必须物理删除。
