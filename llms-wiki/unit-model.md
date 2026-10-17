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

### 内核分层契约（依赖方向冻结）

四个内核模块呈星形单向分层：**transaction 是唯一允许多依赖的编排层，其余三件互不认识**。

```
transaction（编排：唯一可触碰副作用的模块）
 ├─► registry   唯一扫描 configs/ 与 manifest 的模块（蓝图域唯一入口）
 ├─► resolver   纯函数：依赖图进，拓扑序出（零 I/O、零状态，表驱动可测）
 └─► ledger     唯一读写 state.json 的模块（状态域唯一入口）
```

* 禁止绕过 ledger 直写账本，禁止绕过 registry 直读蓝图；
* `resolver` 不 import 任何内核兄弟模块，只做纯计算；
* deploy.atomic、Vault、事件通知、单元生命周期钩子（`post_install` / `post_remove`，
  执行单元目录内 `hooks/<名字>` 脚本）只允许 transaction 触碰；
* doctor 三态对账（`audit_units`：`Synced` / `Drifted` / `Ghost`）是只读能力，
  同样收敛在 transaction（受管文件与哈希知识只此一家），内核保持四模块不变。

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
   - 从 `vault/<unit>/` 捞回自定义文件与最新蓝图合并（捞回即消费：归档移入实机后
     Vault 清空，用户已删除的自定义不会被下次启用复活）；
   - 原子置换进 `~/.config/<target>` 并完成模板渲染；
   - 状态经 ledger 落账 `state.json`，随后发出一次 `unit-changed` 事件（见 §6，尽力而为，无订阅者即 no-op）；
2. **停用动作 (`off` / `disable`)**：
   - 反向依赖检查：若有其他已启用单元依赖它且未带 `--cascade`，强行阻断并报警；
   - 将 `~/.config/<target>` 中的 `__custom__` 与 `preserve` 文件原子移入 `vault/<unit>/`；
   - 彻底删除受管文件，空目录删除，实机恢复纯白；非受管的外来文件不吞——
     幸存并在报告中列明（doctor 记 `Ghost`），绝不背地里吃掉用户文件；
   - 状态经 ledger 落账 `state.json`；
   - 真诚报告交底：明确告知配置已归档，二进制包保留在系统（不背着用户 sudo 卸包）；
   - 发出同一 `unit-changed` 事件，Shell 据此摘除挂件。

### 账本记录形状（KM0 冻结）

`state.json` 中每条单元记录只含五个字段。KM2 的事务与 doctor 对账全部建立在其上，实现不得私加：

| 字段 | 类型 | 含义 |
|---|---|---|
| `state` | `enabled` / `disabled` | 开关轴唯一状态 |
| `preset` | `string` | 形态轴当前选择（预设或零件） |
| `files` | `map<相对路径, sha256>` | 受管文件哈希快照，`Drifted` 判定依据 |
| `vault` | `路径?` | 停用时自定义文件的 Vault 归档位置，`disabled` 时必填 |
| `updated` | `ISO 时间戳` | 最近一次事务落账时间 |

单元记录统一挂在 `state.json` 顶层的 `units` 键下，以单元 ID 为键；`updated` 为带时区的
ISO 8601 时间戳。单元记录的读写只经 `nyxuri.ledger`，任何内核模块不得绕过。

`files` 快照口径（KM2 落地，KM3 扩展）：只记受管文件——`__custom__` 与 manifest
`preserve` 文件属用户心血，不入快照、不参与 `Drifted` 判定；`preserve_values` 目标文件计入；
symlink 记 `link:<目标>`；`post_install` 钩子在快照**之前**运行，钩子落进单元自身生活区
的产物自动入快照、`off` 走正常抹白（钩子落生活区外的产物由 `post_remove` 自清，
见 [manifest-schema](manifest-schema.md) 钩子契约）。停用时无受管快照（`files` 空：从未经事务开关，或停用后
再现内容）的单元按蓝图所有权整域抹白；单文件单元（`target=`）无 Vault 进出，
其唯一实机文件即全部生活区。

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

### 声明边界

manifest 只声明上述字段，不追求覆盖一切。单元的外部副作用走**单元本地钩子**：
`post_install` / `post_remove` 指向 `configs/<unit>/hooks/<名字>` 可执行脚本，
由 transaction 执行（KM3 契约，`<module>:<function>` 旧形态已随 `nyxuri/modules/`
退役；详见 [manifest-schema](manifest-schema.md) 钩子契约）。systemd 服务启停等
跨系统声明字段仍暂不进 manifest：属单元内部行为，出现真实需求再议（登记于
[delayed-decisions](delayed-decisions.md)）。完整字段参考（含 `label` / `category` / `detect` / `optional` / `preserve_values` 等展示与包元数据字段）见 [manifest-schema](manifest-schema.md)。

---

## 5. 四大核心命令

命令行只保留 4 个通用动词（`list`、`on`、`off`、`doctor`），`on` / `off` 另有语义等价长动词（`enable` / `disable`）。不设更短的缩写别名——动词已经够短，别名只是要供养的表面：

```bash
# 1. 查看全景清单或单个详情
nyxuri list [unit]

# 2. 开启单元（支持指定预设）
nyxuri on <unit> [--preset <p>]     # 等价: enable

# 3. 关闭单元（默认拒绝级联，显式 --cascade 才级联关闭下游依赖）
nyxuri off <unit> [--cascade]       # 等价: disable

# 4. 对账检查（实机文件 vs 账本三态审计）
nyxuri doctor [unit]
```

单源阶段**不设独立 `refresh` 动词**：账本即真相，无缓存可刷。

---

## 6. Shell 内部完全单元化与协同契约 (Shell Unitization & Coordination)

> **层次边界**：内核只关心本节三件事——同一账本、单一事件通道、点分 ID。插槽分类学与微内核实现细节属 Shell 侧契约，KM4 Shell 模块化时迁归 [shell 契约](../shell/AGENTS.md)，本页届时只留这三条。
>
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
* **单向事件通知**：事务落账后只发一次 `unit-changed` 事件。这是抽象端口，不是内核命令——当前唯一投递实现是 `quickshell ipc unit reload`，由外层注入，内核不 import、不 subprocess quickshell；无订阅者时为 no-op（测试与无 Shell 环境零负担）；
* **点分 ID 约定**：Shell 域单元以 `shell.<domain>` 命名（如 `nyxuri off shell.dock`），统一挂入 `state.json` 与 4 大动词管辖。内核只认点分 ID 本身，不特判任何前缀。

---

## 7. 深层防御与代码级死刑清单

1. **包管理非对称**：`disable` 只撤回配置与桌面集成，绝不私自调用 sudo 卸载系统包，以避免打断和破坏系统依赖；结果在执行报告中如实写明。
2. **单文件特例一律铲除**：全库 100% 目录平铺化。`configs/starship.toml` 升格为 `configs/starship/`，消灭 sidecar 机制。
3. **Vault 纯文件平铺**：`~/.local/state/nyxuri/vault/<unit>/` 保持目录镜像平铺，不建数据库，不打包压缩，用户肉眼直观可见。
4. **死刑清单与两步执法**：所有过渡物登记在下方清单（名字 + 死刑阶段），契约测试分两步执法：
   - **登记步（KM0 已生效）**：`tests/test_ai_specs.py` 断言清单条目齐全；
   - **执法步**：对应阶段收口时，断言升级为物理删除。升级动作写进该阶段验收步骤（见 ROADMAP），届时登记步对该条目退役。

| 死刑对象 | 死刑阶段 |
|---|---|
| `.optional-apps.toml`（axis-B sidecar） | KM1（已执法） |
| `configs/starship.toml` + `starship.toml.module.toml`（单文件特例） | KM1（已执法，升格为 `configs/starship/` + `target`） |
| `*.module.toml` sidecar 机制（已统一收敛为目录内 `manifest.toml`） | KM1（已执法） |
| `nyxuri/modules/` 专用业务模块（能力并入 `configs/` 单元 + 钩子脚本） | KM3（已执法） |
| 旧 CLI 命令兼容别名（KM3 设倒计时，见 `cli.py RETIREMENTS`） | KM5 |
| `nyxuri/cli.py` 硬编码专用命令 | KM5 |
| `install.sh` 安装器职责（退役为一次性引导） | KM5 |
