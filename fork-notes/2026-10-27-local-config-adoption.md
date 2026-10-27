# 本机配置通过 Nyxuri 命令接管

> 记录日期与冻结日期：2026-10-27。保存本次 Ubuntu 本机接管结果和冲突证据，不作为持续维护的任务台账或其他机器的安装指南。

## 范围与执行方式

环境为 Ubuntu 26.04.1，当前使用 Noctalia，显示管理器为 SDDM；仓库处于 `ubuntu` 分支，
检查时 HEAD 为 `d24374f7af3a95c6e9b1b41885dca306a5966cff`。
`llms-wiki/ubuntu-compatibility.md` 已有一处未提交的路线图锚点修正，本次未修改它。

用户要求配置通过 Nyxuri 命令应用，发现 `on`、`update` 等冲突时报告并记录。
用户明确选择 Kitty 和 Starship 采用仓库默认配置。Zed 和 Portal 使用保存的本机预设，
避免覆盖编辑器个人设置或扩大桌面门户路由的影响范围。

本次所有配置部署均由 `bash /home/laxpud/src/Nyxuri/nyxuri/launcher.sh ...` 执行；
下文以 `nyxuri` 简写。没有手动复制模板到生效目录，没有改写单元账本，也没有修改引擎或单元模板。
保存备份、摘要和日志不属于配置部署。

## 已执行的命令与结果

先执行：

```bash
nyxuri snapshot 'Before command-based adoption 2026-10-27'
nyxuri preset zed save ubuntu-local-20261027
nyxuri preset xdg-desktop-portal save ubuntu-niri-20261027
nyxuri on fastfetch
nyxuri on kitty
nyxuri on starship
nyxuri on zed --preset ubuntu-local-20261027
nyxuri on xdg-desktop-portal --preset ubuntu-niri-20261027
nyxuri on wallpapers
```

随后逐项执行 `nyxuri doctor <unit>`，并在已有未提交修改仍存在的前提下执行一次 `nyxuri update`。

| 单元 | 本次结果 | 生效内容与保留情况 |
| --- | --- | --- |
| fastfetch | 已启用，`Synced` | 默认模板，展示名称由 NyxNiri 改为 Nyxuri |
| kitty | 已启用，`Synced` | 默认主配置；`__custom__.conf`、现有主题文件保留，Maple Mono NF CN 字体保留 |
| starship | 已启用，`Synced` | 默认模板，新增 Noctalia 配色选择与色板 |
| zed | 已启用，`Synced` | 用户预设 `ubuntu-local-20261027`；接管前后全部配置文件内容相同 |
| xdg-desktop-portal | 已启用，`Synced` | 用户预设 `ubuntu-niri-20261027`；现有 Niri 路由与 `.bak` 文件原样保留，未新增全局路由 |
| wallpapers | 已启用，`Drifted` | 所有壁纸内容未变；已有默认壁纸触发对账问题，见下文 |

原有 Niri、Noctalia、theme 仍为已启用、`Synced`。Fish 已在此前接管，本次未重新部署，
仍因个人插件清单显示 `Drifted`。截至本次检查，共 10 个文件类单元登记为启用。

## 冲突与边界

### 1. Fish 的个人插件清单与固定安装钩子不兼容

- **此前已执行的操作**：先 `nyxuri on fish`，再通过原子替换恢复包含 `nvm.fish` 的原插件清单；
  因此此前的 Fish 接管包含一次命令外的个人配置恢复，不能说全过程都仅靠 Nyxuri 命令完成。
- **本次实测**：`doctor fish` 为 `Drifted`；唯一与账本不一致的受管文件是 `fish_plugins`。
- **源码检查**：[Fish 安装钩子](../units/fish/hooks/install-fisher) 只接受三项固定插件清单，
  其他清单会在下载或安装前拒绝。当前清单额外保留 `nvm.fish`，还沿用未带固定版本的 Fisher 名称。
- **对命令的影响**：首次 `on` 会采纳模板清单；已启用后的普通 `on fish` 直接返回。
  普通 `update` 会保留改动清单，但重放钩子时会被拒绝；更新流程未使用钩子返回列表决定整体失败。
  `update --force` 会重新采纳模板清单。
- **结论**：个人插件清单尚无本次验证通过的完整命令部署方案。本次未修复，未执行完整更新来复现钩子失败。

### 2. Kitty 默认快捷键变化及滚轮绑定警告

- **已确认的选择**：用户采用默认快捷键。主配置取消 Ctrl+C 的 `copy_or_interrupt`、
  Ctrl+V 的粘贴和 Ctrl+A 的整段滚屏复制，复制粘贴改用 Kitty 默认的 Ctrl+Shift+C/V。
  主题 include 移到 Custom 之前，个人覆盖可在 Custom 中生效。
- **实际复现**：本机 Kitty 0.45.0 加载配置时报告
  `Mouse button: ctrl+scroll_up not recognized, ignoring` 与对应的 `ctrl+scroll_down` 警告。
  模板中的两条 Ctrl+滚轮字号绑定被忽略。结构解析错误列表为空并不代表这些绑定有效。
- **范围**：这两行在接管前的主配置中也已存在，并非本次新增；它们仍存在于
  [仓库模板](../units/kitty/kitty.conf)。Ctrl+加减号字号绑定不受此警告影响。
- **结论**：默认配置已应用，滚轮绑定兼容问题未修复；没有手动修改实机配置绕过问题。

### 3. Zed 默认模板会覆盖个人行为，使用用户预设接管

默认模板会将 `disable_ai` 改为 `true`，去掉 `vim_mode` 与个人模型设置，并改变字号和面板设置。
本次通过 `preset save` 保存现有配置，再通过 `on --preset` 接管。内容摘要核对一致。

这是 Nyxuri 支持的用户预设路径；该预设保存的是本机完整文件，之后仓库默认 Zed 配置的变化
不会自动合入这些文件。切回默认预设前仍需审阅差异。

### 4. Portal 默认模板扩大路由范围，使用 Niri 专用预设接管

原有用户目录只有 `niri-portals.conf` 和 `portals.conf.bak`。默认单元还会部署
`portals.conf` 与 `mango-portals.conf`，其中全局默认选择 GNOME/GTK；本机还安装了 KDE 的
portal 路由，使用 KDE/KWallet。新增用户级全局路由可能影响其他桌面的后端选择。

本次使用 `preset save` 与 `on --preset` 保持现有文件集合和内容，不重启门户服务。
跨桌面的实际路由变化未复现，因此这里记录的是部署前发现的兼容风险，不声称 Plasma 已出故障。

### 5. 已有默认壁纸导致 merge 部署与 doctor 对账口径不一致

- **实际复现**：执行 `on wallpapers` 成功，所有壁纸的内容摘要前后相同，随后
  `doctor wallpapers` 报 `Drifted`。
- **具体状态**：`lawson_fuji.webp` 在接管前已存在，且与仓库默认文件一致；
  壁纸单元账本的 `files` 为 `{}`。
- **原因**：[merge 部署](../nyxuri/deploy/deploy.py) 遵循不覆盖已有文件的规则，只登记本次实际新增文件；
  [audit_units](../nyxuri/kernel/transaction.py) 却把目录内全部蓝图同名文件的哈希与账本做整体比较。
  这两种集合在本机不相同，导致未改动的壁纸也被标为漂移。
- **结论**：已命令接管，但没有伪造账本消除告警。普通 `on` 再次调用会直接返回；
  依据源码，`update --force` 对已启用壁纸也没有重新收编现有文件的路径，不能照 doctor 的通用提示
  将它当作此问题的修复命令。未实际运行 `--force`。

### 6. update 在脏开发仓库中跳过，退出码仍为 0

- **实际复现**：执行 `nyxuri update` 后提示存在未提交修改，并明确报告
  `Update skipped; source and installed configs were left unchanged.`，退出码为 0。
- **原因**：[safe_git_pull](../nyxuri/pkg/net.py) 对带改动的 repo 模式返回跳过；
  [CLI](../nyxuri/cli.py) 只在拉取成功时重启进入配置部署，跳过时直接正常返回。
- **结论**：保护工作区的行为正常，但命令返回 0 不能作为配置更新成功的验收证据。
  本次没有暂存、提交、隐藏或丢弃已有修改来强行运行更新，配置更新阶段未执行。

### 7. update 的默认部署范围不等于已启用单元

这是**源码检查及只读枚举结果，未执行实机部署复现**。

[更新工作流](../nyxuri/installer/workflows.py) 使用
[discover_deployable_apps](../nyxuri/deploy/manifest.py) 枚举所有含配置的非 merge 单元，
没有先按账本启用状态或 Ubuntu 支持声明过滤。本机枚举结果包含 `fcitx5-rime`、`mango`，
尽管两者未启用，Mango 还明确不支持 Ubuntu。

普通更新会保留已有来源不明的文件，但仍可能补入此前不存在的模板文件；这与“未使用的单元不应用配置”
存在冲突。部署阶段也不经过 `on` 的平台与依赖预检。仓库拉取成功后的非交互流程还会调用
`check_new_deps_post_update()`，可能安装新依赖，因此完整 `update` 不只是文件同步。

本次不通过直接调用内部部署函数代替用户要求的 `update` 命令，也不将源码检查写成更新验收通过。

## 尚未接管的范围

| 对象 | 原因 |
| --- | --- |
| fcitx5-rime | 依赖已满足，但单元目标是 `~/.config/fcitx5-rime`，应用实际读 `~/.config/fcitx5`；直接 `on` 不能代表现有输入法配置已接管。原有迁移边界见 [Ubuntu 指南](../llms-wiki/ubuntu-compatibility.md#fcitx-配置路径限制) |
| mango | 当前 Ubuntu 声明不支持；目录存在，审计为 `Ghost`，未启用或清理 |
| greeter | 当前使用 SDDM，缺少 greetd/Noctalia Greeter；不为了填满账本切换登录管理器 |
| `shell.*` | 当前选择 Noctalia，这些是 Nyxuri 自研 Shell 的运行时单元，不是待接管的配置目录 |
| Ghostty、Bash/Zsh 与共享 shell 定制等 | 当前仓库没有相应单元；既有 chezmoi 管理范围保留，不能声称所有本机配置都已由 Nyxuri 覆盖 |

## 备份、验证与恢复边界

- Nyxuri 快照：`~/.config/nyxuri/backups/snapshot_20261027_100522_865330/`。
  其中 `state-before.json`、`adoption-before-hashes.json`、`adoption-commands.log` 分别保存
  接管前账本副本、有限范围的文件摘要和本轮命令输出；这些本机材料不复制进仓库。
- 先前 Fish 备份：`~/.config/nyxuri/backups/fish-adoption_20261027_094807/`。
- 内容核对：Zed、Portal、全部壁纸保持原样；Kitty Custom 保持原样。
- 应用级检查：Fastfetch 实际运行并显示 Nyxuri；Starship 可渲染提示符；Kitty 配置加载保留字体，
  但有上述两条滚轮绑定警告。未重启应用或门户服务，不将解析成功等同于所有窗口已热重载。
- 使用 `nyxuri snapshot list` 可定位本轮快照。当前 rollback 是整体配置恢复入口，
  快照不自动恢复整个单元账本；若需撤销部分接管，应先明确配置与账本的对应恢复范围，
  不直接把整个 `state-before.json` 覆盖回当前账本。
- 本次没有新增测试、运行全量单测或沙箱部署，没有安装软件、切换显示管理器、提交或推送。
