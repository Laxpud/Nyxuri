# Nyxuri 活跃演进路线

> 本页只保留跨域活跃待办与长期目标；Shell 阶段台账、已确认决策与门禁见
> [shell/ROADMAP.md](shell/ROADMAP.md)。历史全景见
> [archive/roadmap-history](llms-wiki/archive/roadmap-history.md)；
> 设计哲学与五条简洁标准见 [vision](llms-wiki/vision.md)。

## 主线：插件市场化改造

> 当前未启动；前置：Shell P4 验收通过。
> 产品重定义：Nyxuri 从「安装器」收敛为「桌面插件市场」，安装器退役为一次性引导。
> 终态：内核（registry · resolver · transaction · ledger）+ 目录（万物皆单元）+
> 市场界面（TUI 目录浏览器为主，CLI 等价动词）。任何东西——config、模块、壁纸包、
> Shell 域——都是可独立开关的单元：off ↔ on 原子切换，切换前披露、切换后交报告，
> doctor 持续对账「声明 vs 实机」。术语全库统一四词：**单元 / 内核 / 源 / manifest**；
> pacman 与 AUR 包不是单元，是单元声明的依赖。

### 阶段台账

| 阶段 | 交付 | 状态 |
| --- | --- | --- |
| KM0 | 内核契约冻结（`llms-wiki/unit-model.md`） | 待验收 |
| KM1 | 内核落地：注册表与单源目录统一 | 待开始 |
| KM2 | 开关事务与 Vault 归档 | 待开始 |
| KM3 | 命令行收敛（4 动词接管）与 TUI 工坊 | 待开始 |
| KM4 | Shell 彻底模块化 + 运行态直通（吸收原 Shell P5） | 待开始 |
| KM5 | 引导转化、退役清单清空与五原则总验收 | 待开始 |

P6（整体验收与未来移植）保持在 KM5 之后，台账见 [shell/ROADMAP.md](shell/ROADMAP.md)。
KM0 契约已正式上收 [unit-model](llms-wiki/unit-model.md)，全库以此为唯一权威；下方为各阶段实施要点：

- **KM0 内核契约冻结**：四大法定术语（单元 / 内核 / 源 / manifest）；正交状态机（开关与外观严格正交，禁止折叠为互斥假单元）；约定优于配置（无 manifest = 全默认，最小仅 1 行）；Vault 纯文件平铺镜像归档；四大核心动词（`list`, `on`, `off`, `doctor`）；代码级死刑清单制。验收：契约测试 `tests/test_unit_model.py` 全绿。
- **KM1 内核落地**：单源内核落地，坚持减法推迟网络多源；纯标库 `UnitRegistry`、`UnitResolver`、`UnitLedger`（分层契约见 [unit-model](llms-wiki/unit-model.md)）。分两步验收，**删除不寄生于新增**：① registry 落地——新单元接入 = 加目录 + 可选 manifest，零内核代码改动，契约测试改测真实内核（Kahn 参考副本退役）；② v1 物理删除——`.optional-apps.toml`、`starship.toml`、全部 `*.module.toml` 清零，`configs/` 纯平铺，死刑断言升级生效。
- **KM2 开关事务**：`on / off` 原子闭环；反向依赖强阻断与级联关闭；Vault 进出与实机抹白；doctor 对账（`Synced` / `Drifted` / `Ghost` 三态审计）。验收：任一单元停用实机 100% 白纸零残留，自定义文件入 Vault 零丢失。
- **KM3 命令行与 TUI**：4 动词接管全库（`list`, `on`, `off`, `doctor`），旧命令设别名与死刑倒计时；TUI 双栏零件台；退役 `nyxuri/modules/` 专用业务模块。验收：所有能力通用动词闭环，双语文案全量覆盖。
- **KM4 Shell 彻底模块化 + 运行态直通**（吸收原 Shell P5）：Shell 蜕变为纯宿主，业务全部模块化；单一开关真相，Shell 运行态仅为账本投影；单向 IPC 信号触发重绘；原 P5 验收标准平移。验收记录归 shell 台账。
- **KM5 引导转化与终极清算**：`install.sh` 退役为一次性引导脚本；契约测试强制触发死刑断言，物理删除旧命令兼容层；五原则逐条给出可复现证据。验收：退役清单清空为零，仓库代码实现净减法。

### 全局门禁（每阶段验收都过）

1. **单一开关真相**：所有界面（CLI、TUI、Shell 设置）都是同一张开关的投影，翻转状态只走同一条事务路径落 `state.json`；Shell 不持有私有状态。
2. **桥接零新通道**：市场 ↔ Shell 运行态通知只复用 Shell 既有 IPC 通道，不新增第二条。
3. **单元边界**：能力不设限，副作用必须声明——单元内部可管服务、写 `/etc`、装包，但一切外部效果必须写进 manifest；单元之间只走声明的依赖。
4. **退役清单制**：每个过渡物（CLI 别名、旧安装流程、`.optional-apps.toml`、`engine_is_complete` 清单）登记名字与死刑阶段；清单不空，KM5 不算完成。
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
- [ ] **多合成器 (Multi-WM) 架构解耦**：`CompositorDriver` 驱动抽象层，热重载、浮动便签与屏幕探测跨合成器适配（Hyprland/Sway 按需扩展），`doctor` 诊断与 `greeter` 会话自适应。现状：niri + mango 双合成器已以过渡形态落地（引擎特判与收编清单见 [mango-adaptation](llms-wiki/mango-adaptation.md) 债务登记），第三个合成器接入前必须收编为驱动抽象。
- [ ] **安全 Downdate 体系（高级储备）**：现场快照优先还原 + Git 逆向检出的安全版本回退。
