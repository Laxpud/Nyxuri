# Operation Map — 全部 CLI 命令

> 命令分发在 `nyxuri/cli.py` 的 `COMMANDS` dict。退出码自动传播。aliases 并列。
> KM3 起命令表收敛为 4 个通用动词（list / on / off / doctor），详见
> [unit-model](unit-model.md)；其余命令按 [§退役倒计时](#退役倒计时-unit-model-7) 排期执法。

## 单元动词（4 动词接管）

| 命令 | 干啥 |
|---|---|
| `list [unit]` | 单元全景（开关状态 × 当前预设），或单个单元详情（manifest 声明 × 账本记录 × 对账态） |
| `on <unit> [--preset <name>]`（等价 `enable`） | 启用单元：依赖闭包披露 → 缺失包披露确认（repo/AUR/Flatpak 按 manifest 三方分流）→ 事务落账 + `unit-changed` 事件 |
| `off <unit> [--cascade]`（等价 `disable`） | 停用单元：反向依赖强阻断（显式 `--cascade` 才级联）→ 自定义入 Vault → 实机抹白；报告列明幸存外部文件与保留的包 |
| `doctor [unit]` | 单元三态对账（`Synced` / `Drifted` / `Ghost`）；无参时在对账表后附加系统体检段（原 `_check_*` 收编为附属段） |

切换前披露、切换后交报告是产品定论：`plan_on` / `plan_off`（只读）供界面披露，
写入只走 `transaction.unit_on` / `unit_off` 唯一事务路径。

## 管"配置内容"的

| 命令 | 干啥 |
|---|---|
| `install [full|config]`（alias `deploy`） | 部署配置（full = + 壁纸 + 模块）；市场化后由 `on <unit>` 接管 |
| `update [--force|--no-deploy] [--to <tag|commit>]` | 拉新版本 + 线性状态迁移 (`migrations`) + 重新部署；`--to` 锁到指定版本（system 模式 → 提示 pacman） |
| `preset <app> [list|apply <name>|save <name>|edit <name>|delete <name>|parts|part <slot> <name>]` | 切/管理预设与零件插槽（状态接入 `state.json` 账本） |

## 管"安装方式"的

| 命令 | 干啥 |
|---|---|
| `deps [core|apps]` | 装软件包 |
| `apps`（alias `recommended`） | 装可选软件 |
| `pkg <install|upgrade|remove|search|info|installed>` | Fish 与安装器共用包管理；安装接收包名，搜索支持 `aur` / `pac` 前缀 |
| `wallpapers`（alias `wp`） | 装壁纸包（维护 `.nyxuri-managed.json` 跟踪清单） |
| `greeter` / `fcitx` / `gtk` / `fisher` `[install|status|uninstall]` | 扩展模块管理（KM3 随 `nyxuri/modules/` 死刑退役，能力并入对应单元走 `on`/`off`） |
| `theme [toggle|dark|light|sync|status]` | 原生切换/同步深浅主题（纯 Python 调度 gsettings、GTK settings.ini、Noctalia IPC 与 Kitty 信号，status 查询当前模式） |

## 管"状态"的

| 命令 | 干啥 |
|---|---|
| `snapshot [note|list]`（alias `backup`） | 存档当前配置；`snapshot list` 列出存档（旧裸 `list` 已让位给单元清单） |
| `snapshot delete [index]` | 删除快照 |
| `rollback [index]`（alias `restore`） | 从存档恢复 |
| `shell [get|set <noctalia|nyxuri-shell> [bin_path]|switch [<noctalia|nyxuri-shell> [bin_path]]|status]` | 查看或切换桌面外壳运行插槽（switch 无参在 noctalia 与 nyxuri-shell 间互切；兼容 custom/nyxuri 别名，记录于 state.json 账本）。**[EXPERIMENTAL]** nyxuri-shell 完全在开发中、暂不推荐日常使用，切换与状态输出会带实验性警告；已知问题见 [shell/KNOWN-ISSUES.md](../shell/KNOWN-ISSUES.md) |
| `clean [-n] [--only <任务>]` | 缓存清理；`-n` 只预览，Fish 的 `clean` 指向此入口 |
| `uninstall [--all|standard|restore|purge]`（alias `remove`）/ `purge` | 卸载（勾选式） |
| `bug`（alias `report`） | 导出诊断报告 |
| `test` | 开发者沙箱部署测试 |
| `help` | 用法 |

## 退役倒计时 (unit-model §7)

每个条目在 `nyxuri/cli.py` 的 `RETIREMENTS` 表登记（旧名 → 替代能力 → 执法阶段），
调用时打印一行倒计时告警；执法阶段物理删除并退役登记行。

| 旧命令 | 替代能力 | 执法 |
|---|---|---|
| `greeter` / `fcitx` / `gtk` / `fisher` | `on`/`off` 对应单元（greeter / fcitx5-rime / noctalia / fish） | KM3 |
| `deploy` | `on <unit>` | KM5 |
| `backup` / `restore` | `snapshot` / `rollback` | KM5 |
| `remove` / `purge` | `uninstall` / `uninstall purge` | KM5 |
| `recommended` | `on <unit>` | KM5 |
| `wp` / `report` | `wallpapers` / `bug` | KM5 |

## 三层配置模型是内容侧的灵魂

三层（configs < presets < customs）是内容侧，其他都是围绕它的操作。详见
[overview](overview.md)、[preset-mechanism](preset-mechanism.md)。

## 兼容别名

在全局更名迁移期内，系统软链接与用户端别名 `nyxniri` 完全保留，执行任何命令均等价于 `nyxuri`，且自动兼容 `NYXNIRI_*` 环境变量。
