# Nyxuri 活跃演进路线

> 本页只保留跨域活跃待办与长期目标；Shell 阶段台账、已确认决策与门禁见
> [shell/ROADMAP.md](shell/ROADMAP.md)。历史全景见
> [archive/roadmap-history](llms-wiki/archive/roadmap-history.md)；
> 设计哲学与五条简洁标准见 [vision](llms-wiki/vision.md)。

## 主线：插件市场化改造

> 推进中：KM0–KM3.5 已全数落地验收，当前演进目标为 KM4。
> 产品重定义：Nyxuri 从「安装器」收敛为「桌面插件市场」，安装器退役为一次性引导。
> 终态：内核（registry · resolver · transaction · ledger）+ 目录（万物皆单元）+
> 市场界面（TUI 目录浏览器为主，CLI 等价动词）。任何东西——config、模块、壁纸包、
> Shell 域——都是可独立开关的单元：off ↔ on 原子切换，切换前披露、切换后交报告，
> doctor 持续对账「声明 vs 实机」。术语全库统一四词：**单元 / 内核 / 源 / manifest**；
> pacman 与 AUR 包不是单元，是单元声明的依赖。

### 阶段台账

| 阶段 | 交付 | 状态 |
| --- | --- | --- |
| KM0 | 内核契约冻结（`llms-wiki/unit-model.md`） | 已完成 |
| KM1 | 内核落地：注册表与单源目录统一 | 已完成 |
| KM2 | 开关事务与 Vault 归档 | 已完成 |
| KM3 | 命令行收敛（4 动词接管）与 TUI 工坊 | 已完成 |
| KM3.5 | 拆迁与正名（KM5 前置）：旧世界处决 + 文件树表达架构 | 已完成 |
| KM4 | Shell 彻底模块化 + 运行态直通（吸收原 Shell P5） | 待开始 |
| KM5 | 引导转化（installer/ 处决 + install.sh 引导化）、migrations 清算与五原则总验收 | 待开始 |

P6（整体验收与未来移植）保持在 KM5 之后，台账见 [shell/ROADMAP.md](shell/ROADMAP.md)。
KM0 契约已正式上收 [unit-model](llms-wiki/unit-model.md)，全库以此为唯一权威；下方为各阶段实施要点：

- **KM0 内核契约冻结**：四大法定术语（单元 / 内核 / 源 / manifest）；正交状态机（开关与外观严格正交，禁止折叠为互斥假单元）；约定优于配置（无 manifest = 全默认，最小仅 1 行）；Vault 纯文件平铺镜像归档；四大核心动词（`list`, `on`, `off`, `doctor`）；代码级死刑清单制。验收：契约测试 `tests/test_unit_model.py` 全绿。
- **KM1 内核落地**：单源内核落地，坚持减法推迟网络多源；纯标库 `UnitRegistry`、`UnitResolver`、`UnitLedger`（分层契约见 [unit-model](llms-wiki/unit-model.md)）。分两步验收，**删除不寄生于新增**：① registry 落地——新单元接入 = 加目录 + 可选 manifest，零内核代码改动，契约测试改测真实内核（Kahn 参考副本退役）；② v1 物理删除——`.optional-apps.toml`、`starship.toml`、全部 `*.module.toml` 清零，`configs/` 纯平铺，死刑断言升级生效。
- **KM2 开关事务**：`on / off` 原子闭环；反向依赖强阻断与级联关闭；Vault 进出与实机抹白；doctor 对账（`Synced` / `Drifted` / `Ghost` 三态审计）。验收：任一单元停用实机 100% 白纸零残留，自定义文件入 Vault 零丢失。
- **KM3 命令行与 TUI**：4 动词接管全库（`list`, `on`, `off`, `doctor`），旧命令设别名与死刑倒计时；TUI 双栏零件台；退役 `nyxuri/modules/` 专用业务模块。验收：所有能力通用动词闭环，双语文案全量覆盖。
- **KM3.5 拆迁与正名**（KM5 前置）：三世代同屋檐的总清算——处决在册死刑犯（旧命令别名 ×12、`RETIREMENTS` 整表、`template_registry.py`、17 个零文件假单元、`assets/` 旁路）；蓝图正名 `configs/` → `units/`（壁纸升格单元、假单元数据收敛 `catalog.toml`）；引擎物理分层（`kernel/` · `desktop/` · 供给收编 `pkg/`、微文件清零、`installer/` 等死区隔离）；测试镜像源码树；llms-wiki 29 → ≤15 页。实施要点见下方专节。
- **KM4 Shell 彻底模块化 + 运行态直通**（吸收原 Shell P5）：Shell 蜕变为纯宿主，业务全部模块化；单一开关真相，Shell 运行态仅为账本投影；单向 IPC 信号触发重绘；原 P5 验收标准平移。验收记录归 shell 台账。
- **KM5 引导转化与终极清算**：`install.sh` 退役为一次性引导脚本，并处决 `nyxuri/installer/` 等死区（workflows / menus 隔离件）；`migrations/` 旧版迁移清算；契约测试强制触发死刑断言，物理删除旧命令兼容层；五原则逐条给出可复现证据。验收：退役清单清空为零，仓库代码实现净减法。（拆迁主体已前置至 KM3.5，本阶段只剩引导收口与总验收。）

### KM3.5 拆迁与正名（KM5 前置）

> 起因：KM0–3 后仓库仍三个世代同屋檐——安装器残余与内核、Shell 世代交错平铺，
> 文件树不表达架构，透明必须靠读完契约才能获得。本阶段把 KM5 的拆迁前置执行：
> 先处决、再正名，一次契约同步。验收后 KM5 只剩引导收口与总验收。

**处决清单（全部登记在册，本阶段执法）**：
旧命令别名与幽灵指针 ×12（`deploy/backup/restore/remove/purge/recommended/wp/report`
+ `greeter/fcitx/gtk/fisher`）、`RETIREMENTS` 整表、`template_registry.py`
（生产零引用）及其测试、`configs/` 下 17 个零文件假单元、`assets/` 与
`deploy/assets.py`。

**正名与分层（文件树即架构，每项一行「为什么在这」）**：

| 对象 | 现状 | 终态 |
|---|---|---|
| 蓝图 | `configs/` 28 目录 | `units/` 12 目录：11 真单元 + `wallpapers/`（assets 升格；自研工具按决议留在 noctalia） |
| 假单元数据 | 17 个零文件目录冒充单元 | 根 `catalog.toml`（`deps` 菜单与 gen-deps optdepends 同源；契约补「包目录清单不是单元」） |
| 内核 | 四模块平铺埋没 | `nyxuri/kernel/`（契约 §2 物理承载修订） |
| 供给 | `deps.py`、`network.py` 游离，`pkg/cli.py` 撞名 | 全部收编 `nyxuri/pkg/`（deps · detection · net · fzf） |
| 地基 | `core.py` + `constants.py` + `i18n.py` 三散件 | 并入单一 `core.py`（顶层无微文件） |
| 诊断 | `doctor.py` 与对账 doctor 重名 | `sysdoctor.py` |
| 桌面能力 | theme / shell_switcher / clean 散落 | `nyxuri/desktop/`；clean.py 能力保留，拆除自带私人 i18n/颜色/宽度微框架，接 `nyxuri.i18n` 与 tui 原语（710 → ~500，功能零变化） |
| 预设机制 | `deploy/preset.py` 918 行引擎与动词业务混居 | 引擎半（继承/staging/fd 安全）留 deploy；apply/save/delete/edit 流程迁出 deploy 层，渲染一律归 UI 域 |
| 安装器 | workflows / menus 居引擎顶层 | `nyxuri/installer/` 等死区——KM5 随 install.sh 引导化整目录处决 |
| 构建 | `nyxuri/packaging/` 混进运行时包 | 仓库根 `packaging/` |
| 测试 | 62 文件平铺，18 个 translate 淹没根目录 | 镜像源码树约 40 文件：`kernel/ deploy/ pkg/ state/ desktop/ tools/translate/{core,catalog,tui}`，契约测试置顶，bugfix 抽屉拆散归位 |
| 文档 | llms-wiki 根 29 页（三世代重叠） | ≤15 页：`assets-deploy` / `install-modes` / `two-axis-config` / `tui-switcher` 归档 `archive/`；`concept-glossary` 并入 unit-model、`declarative` 并入 manifest-schema、`runtime-topology` 并入 overview；其余逐页过 docs-charter，答不出「为什么在这」即合并或归档；AGENTS.md 路由同波更新；humans-wiki CLI-Reference 重写到动词世界；overview.md 重写为一页仓库地图 |

**配套修复**：
单元钩子注入 `PYTHONDONTWRITEBYTECODE=1`（蓝图「源码绝对只读」不变量，P0）；
manifest `target` 支持 `~/` 前缀（壁纸单元落 `~/Pictures/Wallpapers`，外部包下载转
`hooks/install-pack`，`wallpapers` 动词处决并指向 `on wallpapers`）。

**终态一屏图（验收即对照）**：

```
Nyxuri/
├─ nyxuri/            引擎 · 12 项
│   ├─ kernel/ deploy/ pkg/ state/ desktop/ installer/ migrations/
│   └─ cli.py core.py translations.toml sysdoctor.py tui.py
├─ units/             蓝图 · 12 真单元
├─ shell/ tests/ llms-wiki/ humans-wiki/ packaging/
└─ catalog.toml install.sh
```

**验收（2026-10-17 执法记录）**：处决清单全数落地——旧命令别名 ×12 与
`RETIREMENTS` 整表、`template_registry.py` 及其测试、17 个零文件假单元（→ 根
`catalog.toml`，`deps apps` 菜单与 gen-deps optdepends 同源）、`assets/` 与
`deploy/assets.py`（→ `units/wallpapers/` 真单元：`target ~/` + `merge` 共享生活区，
pack 下载转 `hooks/install-pack`，`wallpapers` 动词处决指向 `on wallpapers`，
`.nyxuri-managed.json` 退役）、`apps` 伪装别名与 `-h/--help`；蓝图正名 `configs/` →
`units/`（12 目录），内核物理承载 `nyxuri/kernel/`，供给收编 `pkg/{deps,net,fzf,catalog}`，
地基三合一 `core.py`，`doctor.py` → `sysdoctor.py`，桌面域 `desktop/`（clean 接
i18n/tui 原语），`installer/` 等死区隔离，preset 引擎/流程拆分（`deploy/preset.py` +
`desktop/presets.py`），`packaging/` 迁仓库根，测试镜像树（62 平铺 → 55 镜像 +
契约测试置顶），llms-wiki 根 30 → 15 页；单元钩子注入 `PYTHONDONTWRITEBYTECODE=1`。
全量契约测试绿 + 沙箱部署绿 + shellcheck 绿。install.sh 引导化与 migrations 清算
不在本阶段，仍留 KM5。

**数字对账（如实）**：CLI 32 → 20 ✓；蓝图 28 → 12 ✓；`nyxuri/` 顶层 26 → 12 ✓；
llms-wiki 根 30 → 15 ✓；测试 62 → 55 ✓（~40 为估算，translate 16 文件保持内聚
未强行合并）；**引擎净删 -259 行（毛删 1,590），低于 ≥900 目标**——处决照单全收，
但 `merge` 共享生活区语义、`catalog.toml` 解析器、preset 引擎/流程拆分三项配套
合法新增约 +1,300 行，原估算未计入；不为凑数删活代码，差距留 KM5 引导化收口时
随 `installer/` 整目录处决一并回收。

**验收（五原则证据 + 净减法）**：
引擎净删 ≥900 行；CLI 表面 32 → 20 条目（17 活动词 + help）；蓝图 28 → 12 目录；
`nyxuri/` 顶层 25 → 12 项；llms-wiki 根 29 → ≤15 页；测试 62 平铺 → 镜像树 ~40；
全量契约测试绿 + 沙箱部署绿。install.sh 引导化与 migrations 清算不在本阶段，仍留 KM5。

### 全局门禁（每阶段验收都过）

1. **单一开关真相**：所有界面（CLI、TUI、Shell 设置）都是同一张开关的投影，翻转状态只走同一条事务路径落 `state.json`；Shell 不持有私有状态。
2. **桥接零新通道**：市场 ↔ Shell 运行态通知只复用 Shell 既有 IPC 通道，不新增第二条。
3. **单元边界**：能力不设限，副作用必须声明——单元内部可管服务、写 `/etc`、装包，但一切外部效果必须写进 manifest；单元之间只走声明的依赖。
4. **退役清单制**：每个过渡物（CLI 别名、旧安装流程、`nyxuri/modules/`、`engine_is_complete` 清单）登记名字与死刑阶段；清单不空，KM5 不算完成。
5. **五原则验收**：阶段收口按 [vision](llms-wiki/vision.md) 五条标准给出可复现证据（真诚透明 / 绝对主权 / 骨架包容 / 轻盈生长 / 通用自然）。

### 已确认的设计定论（KM0 决议）

全部决议已上收 [unit-model](llms-wiki/unit-model.md)（分层契约、账本记录形状、事件通道、无 `refresh` 动词、死刑清单与两步执法），此处不再复述。仅存一条节奏定论：外部源 KM1 仅建 `local:builtin` 单一本地抽象，网络多源推迟至整体系统稳固后。

### 储备（不承诺）

- 第三方源信任分级与签名。
- 多合成器、安全 Downdate 等长期储备沿「Shell 后生态」条目，市场化后以单元形态实施，不在两处重复展开。

## 自研 Shell（当前：P4 主题契约）

- 阶段台账与当前进度：见 [shell/ROADMAP.md](shell/ROADMAP.md)，此处不复述。
- [ ] **原生壁纸管理与 MD3 取色内生**：壁纸域自治之上取色引擎可插拔——短期经契约层走 matugen，长期以 material-color-utilities 纯 JS 移植替换并退役 matugen，直出色板契约、无外部取色二进制（P4 落契约、后置收口；启动器与壁纸域已在 R4-C 完成代码自治）。
- [x] **六大标准动作与双 Shell 切换**：`launcher` / `session` / `settings` / `clipboard` / `lock` / `wallpaper-random` 经 `shell-action.sh` 零改动响应；`nyxuri shell set` 热切换与异常安全回滚已交付（P1/P2，证据见 Shell 台账）。
- [ ] **Noctalia Template 兼容与主题契约 (TemplateAdapter)**：落地 palette JSON 色板契约与 Noctalia 模板规范（`{{ }}` 表达式、`<* *>` 块与过滤器）适配层，GTK CSS、Fcitx5、Kitty、Starship 和用户模板无需重写；深浅模式系统同步收敛到 `nyxuri theme` 单一实现；运行时不依赖 noctalia 二进制（P4 交付）。
- [ ] **Noctalia + Wallpaper Picker 协同稳固验收**：双轨方案互不干扰、各自纯白——原 P5 验收项，随 P5 吸收为主线 KM4 验收。

## Shell 后生态

- [ ] **TUI 视觉风格化与纯净感 (Terminal Rice)**：Alternate Screen Buffer 保护终端历史，DEC 2025 协议消除高刷频闪，单行微动 Zen Spinner 就地收拢滚屏日志。
- [ ] **多合成器 (Multi-WM) 架构解耦**：`CompositorDriver` 驱动抽象层，热重载、浮动便签与屏幕探测跨合成器适配（Hyprland/Sway 按需扩展），`doctor` 诊断与 `greeter` 会话自适应。现状：niri + mango 双合成器已以过渡形态落地（引擎特判与收编清单见 [delayed-decisions](llms-wiki/delayed-decisions.md) 债务登记），第三个合成器接入前必须收编为驱动抽象。
- [ ] **安全 Downdate 体系（高级储备）**：现场快照优先还原 + Git 逆向检出的安全版本回退。
