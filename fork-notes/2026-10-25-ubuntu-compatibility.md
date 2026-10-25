# Ubuntu 兼容开发与验收记录

> 记录日期：2026-10-24 至 2026-10-25；冻结日期：2026-10-25。
> 原位置：`llms-wiki/ubuntu-compatibility.md`，另收录本次任务的范围决定。
> 本文保存当时的开发与实机验收事实，不作为现行安装指南或持续更新的任务台账。

现行说明见 [Ubuntu 兼容指南](../llms-wiki/ubuntu-compatibility.md)，任务状态见
[ROADMAP](../ROADMAP.md#ubuntu-兼容)，记录分工见
[fork 协作规则](../llms-wiki/fork-workflow.md#文档分工与开发记录)。
各阶段的“本轮”“未执行”“待验收”均指该阶段当时的情况；后续验证不会改写前面的历史结论。
以下临时路径仅供追溯，不保证文件长期存在；未将原始日志、截图或机器配置复制进仓库。

2026-10-25 迁移校对：将原文“下文”的 Fcitx 引用改为现行指南链接，未改变验收结论。

## 范围决定

本次在 `ubuntu` 分支完成 Ubuntu 包后端及 Niri 会话适配，不切换显示管理器，
不编译缺少预编译来源的依赖，不永久安装验收用的临时 Quickshell。
2026-10-25 用户确认保留原有 Fcitx 单元目标目录契约，只记录其缺陷，不迁移
目标路径、单元分类或已有账本；现有 Fcitx 配置的实机输入通过不能代替新安装验收。

## Quickshell 包依赖调查（2026-10-25）

本机 Dank Linux PPA 的 Quickshell `0.3.2ppa1` 只依赖 Qt 共享库，没有传递安装
Shell 的 QML import 模块。`catalog.toml` 的 Ubuntu 条目因此另列
`qml6-module-qtquick-controls`、`qml6-module-qtquick-effects`、
`qml6-module-qtquick-layouts`、`qml6-module-qtcore`、
`qml6-module-qt-labs-folderlistmodel` 和 `qml6-module-qt5compat-graphicaleffects`。
其中 Controls 经 APT 依赖提供 QtQuick、QtQml、Shapes、Templates 和 Window，
QtQml 再提供 Models 与 WorkerScript。Qt5Compat 提供 Shell 使用的
`Qt5Compat.GraphicalEffects`，仅有 Qt6 共享库不能代替这些 QML 插件。

## 软件来源与跳过清单

以下为 2026-10-24 在 Ubuntu 26.04 本机查询的来源情况。`apt-cache policy` 反映
当前配置的源和缓存，不是全互联网的软件存在性证明。以后执行安装仍重新查询候选。

### 无已接入预编译来源、跳过构建的依赖

| 依赖 | 当前处理 | 受影响能力 |
| --- | --- | --- |
| `mpvpaper` | 当前配置的 APT 源无候选，声明为手动依赖；不执行本机源码编译。已有可用命令时接受 | 视频壁纸播放与同步；不阻断静态壁纸文件部署 |
| Mango / `mangowm` | Ubuntu 单元标为不支持；官方安装页未列 Ubuntu 预编译路线，其他平台之外给出源码构建方式，本任务跳过 | Mango 会话，不影响 Niri 路线 |

Mango 来源：[官方安装说明](https://mangowm.github.io/docs/installation/)。

### 有预编译包或资源，但需要额外来源/手动准备

| 项目 | 供应方式与当前边界 |
| --- | --- |
| Niri、Quickshell | 本机 Dank Linux PPA 有候选；清洁 Ubuntu 不能假定已经配置该源。运行时按需安装 |
| Noctalia、Noctalia Greeter | 本机 Noctalia APT 源有候选；greeter 服务切换不是普通依赖安装的一部分 |
| Brave Origin | 官方提供 `brave-origin` APT 包，本机尚无候选；需要另行配置其来源，不把它当成必须编译 |
| VS Code | 使用微软源中的 `code`；本机该源已配置 |
| FlClash、Motrix | 上游提供预编译 DEB；当前标为手动提供，安装后需要对应命令出现在 PATH |
| Zed | 上游提供预编译二进制；当前标为手动提供 `zed`，不执行其远程安装脚本 |
| Rime Ice | 上游提供方案资源压缩包，不是本机编译依赖；准备 `rime_ice.schema.yaml` 及配套词库后再启用输入法单元。不要清空用户现有 Rime 数据 |
| JetBrains Mono Nerd Font | 当前源无对应包，作为字体资源手动提供；普通 JetBrains Mono 字体不能代替 Nerd Font 图标 |
| Material Symbols Rounded / Outlined | 使用 Google 官方预编译 TTF；Nyxuri Shell 的两个字族均需由 Fontconfig 实际识别，普通 Material Icons 不能代替 |
| Mission Center、Telegram、ProtonPlus、QQ、Spotify、WeChat | 使用声明的 Flathub app ID；Flatpak 独立安装，不转译为原生包名 |
| Shelly | Arch/pacman 专用工具，Ubuntu 不支持该条目；Ubuntu 使用本项目 APT 后端 |

来源：[Noctalia](https://docs.noctalia.dev/noctalia/getting-started/installation/)、
[Brave Origin](https://brave.com/origin/linux/)、[VS Code](https://code.visualstudio.com/docs/setup/linux)、
[FlClash](https://github.com/chen08209/FlClash)、[Motrix](https://github.com/agalwood/Motrix/releases)、
[Zed](https://zed.dev/docs/linux)、[Rime Ice](https://github.com/iDvel/rime-ice/blob/main/README.md)、
[ProtonPlus](https://github.com/Vysp3r/ProtonPlus/blob/main/README.md)、
[Shelly](https://github.com/Seafoam-Labs/Shelly-ALPM)、
[Mission Center 的 Flathub 条目](https://flathub.org/en/apps/io.missioncenter.MissionCenter)、
[Telegram 官方下载](https://desktop.telegram.org/)。

## 本轮验证记录（2026-10-24）

- 既有全量测试在只读根目录、独立 HOME/XDG 和 Arch 发行版视图中运行：
  共运行 965 项，结果通过（19 项跳过）。发行版视图用于执行原有 Arch 包管理契约；Ubuntu 路径另行实测。
- Ubuntu 原生路径：`pkg installed/info/search`、已安装包跳过安装、无候选包拒绝、
  AUR 拒绝均符合预期；`on kitty → doctor kitty → off kitty` 完成。
- 独立 HOME 中启用 Niri、portal 和 Noctalia 配置；部署后的 `niri validate` 通过。
  Noctalia 守护进程未运行，GTK 渲染钩子明确报告未完成。`test` 隔离部署通过。
- 聚合会话工具链及 Niri、Noctalia、终端、Fcitx、portal 的原生包做 APT 模拟：
  可解，1 项升级、1 项新增、0 项移除；未执行系统安装。
- 独立 HOME 的 PTY 交互完成主菜单 → 软件与依赖 → 核心依赖 → 返回/退出，
  Ubuntu 包状态正常显示；退出恢复光标并关闭鼠标跟踪。
- `compileall`、Bash/Fish 语法、ShellCheck 与差异空白检查通过。
  ShellCheck、Quickshell 与 cliphist 只解包到临时目录，不注册到系统。
- Quickshell 0.3.2 的版本查询通过；无 Wayland 会话的 offscreen 启动在
  `IdleInhibitorSurface` 报 `No PanelWindow backend loaded`。该检查未证明 Shell
  可用，图形与 IPC 验收保留在 Niri 清单。
- Ubuntu `doctor` 的桌面检查结果为 23 项通过、9 项警告、1 项错误（当前不在受支持
  合成器内）。这里没有把 Plasma 环境下的完整桌面健康度记为通过。

原始命令记录保存在本轮临时目录 `/tmp/nyxuri-ubuntu-evidence/`，全量测试日志为
`/tmp/nyxuri-ubuntu-arch-suite.log`；临时文件清理后，以本节记录和重新执行结果为准。
本轮未新增测试、未修改真实用户配置、未切换显示管理器。

## 上游同步验证（2026-10-25）

合入 upstream/main `62b1479` 的 32 个提交。保留 Ubuntu 包后端与依赖映射，
接纳上游的部署文件保留、更新入口与缓存清理改进；Fcitx 目录问题仍按已确认边界保留。

- 针对部署、manifest、事务、CLI、包管理、文案及清理运行 242 项既有检查。
  240 项直接通过；两项 Arch 清理用例需要补齐本机缺少的 `pacman` 命令探测条件，
  补齐后通过。未修改测试文件；该环境补充不代表 Ubuntu 存在 pacman。
- Ubuntu 原生路径的包查询、kitty 启停/对账、Niri 部署后配置校验、APT 清理预览和
  10 个配置的隔离部署通过。未执行系统安装、真实清理或图形会话切换。
- 修正上游工作流中缺少的 `Optional` 导入，保留 Python 3.11+ 的注解名称解析。
  新设置界面的 Niri 实机验收仍未进行，不能由这些检查替代。

## Niri 会话中的验证记录（2026-10-25）

在本机 Ubuntu 26.04.1、Niri 会话与 Noctalia 5.3 中完成下列检查。
本节只记录已发生的结果；本轮核心交互与新登录验收已完成，已知限制分别注明。

- 修复 Orbit 的 GI Cairo 依赖和诊断、GTK3 不支持的 `color-mix()`、单独启用单元时
  未渲染 `/home/user` 的路径，以及 Shell 入口发现、只读 IPC 清缓存和锁态返回类型。
- 补齐 Ubuntu Quickshell 的 QML 模块与两个 Material Symbols 字族声明；修复
  QML JS 跨文件导入、旧属性和录屏胶囊 shader 路径。实际设置窗口、启动器、会话菜单、
  侧栏能加载；最终截图中的文字与图标正常，设置窗口按 Niri 规则浮动。
- 临时 HOME/XDG、独立 D-Bus 和进程命名空间中，Noctalia → 自研 Shell → Noctalia
  切换及退出清理通过。使用本机静态壁纸生成 GTK3/4 样式，两份样式均通过实际 GTK
  解析。Quickshell 仍来自临时解包目录，未注册为系统软件包；key-cli 缺席时的剪贴板、
  系统监控等功能不在本次核心窗口验收结论内。
- 实际部署前备份受影响配置与状态到
  `~/.local/state/nyxuri-compat-backups/20261025-112008/`，随后依次启用 theme、
  noctalia、niri，三个单元的 doctor 均为 Synced。5 个现有自定义/显示器配置哈希
  不变，旧 Orbit 自定义菜单保留并复制到 Noctalia 工具读取的位置。Niri 配置校验、
  当前 GTK3 样式解析通过，横屏/竖屏的位置、缩放和旋转不变。
  用户随后确认双屏上的 Orbit 图标与指针定位、Super+A 和 Scratchpad 开关/定位均正常。
- 本次人工维护将两个官方 Material Symbols TTF 安装到用户字体目录；自动依赖流程
  仍只检测。Noctalia、Fcitx 原有进程继续运行，默认 Shell 保持 Noctalia。
- Noctalia 启动器、剪贴板面板、设置窗口和通知 IPC 可用；portal 文件选择窗口实际
  打开并取消；Wayland 剪贴板标记往返成功并恢复原内容，Niri 截图生成有效 PNG。
  屏幕共享来源选择器能正确列出横竖双屏。用户授权后，Zen 浏览器的
  `getDisplayMedia` 取得完整 2560×1440 桌面帧，预览正常，随后自动结束共享，
  Niri 中无残留 cast。本地验收页与结果位于 `/tmp/nyxuri-browser-cast/`，服务已退出。
  简单 GStreamer CPU 管线不接受 Niri 的 DMA-BUF 格式；加入 GL 转换后能取帧，
  但本机仍为黑图。该管线结果不能代替已通过的浏览器验收，也不能据此承诺所有
  GStreamer 录屏应用正常；相关格式限制见 [上游问题 4393](https://github.com/niri-wm/niri/issues/4393)。
- portal Screenshot 在当前双屏上失败，Niri 日志为 `outputs.len() == 1 (2 vs 1)`。
  [Niri 26.04 源码](https://github.com/niri-wm/niri/blob/v26.04/src/niri.rs#L5298-L5310)
  的 `screenshot_all_outputs` 明确只接受单输出，尚未处理多缩放和裁剪；这不影响
  已通过的 Niri 单屏截图路径。本轮不替换或编译合成器，也不关闭用户显示器来规避验收。
- 用户确认 Super+L 锁屏、解锁及 Kate/Zen 中文输入正常。随后 Nautilus 输入/搜索
  出现卡顿，现场主线程持续占用一个 CPU 核心，Fcitx IPC 正常。用户提供的调用栈，
  经匹配本机 GTK Build ID 的 Ubuntu 调试符号解析，停在搜索结果更新经过的
  `gtk_list_item_manager_ensure_items` → `gtk_rb_tree_node_get_next` 路径。
  这是已定位的卡顿位置，尚未确认触发缺陷。重开后，用户多次复验 Ctrl+L 地址栏和
  Ctrl+F 搜索框中文输入正常，日志未记录相同卡顿；不能宣称已修复该偶发问题，
  也不据此归因于原有 Fcitx 单元目录问题。现场版本为 Nautilus 50.2.2、GTK 4.22.4。
- 既有部署/事务/单元模型的定向用例使用原有 Arch 平台夹具后通过；直接以 Ubuntu
  运行时，部分旧夹具缺少 Ubuntu 包映射，不能把该结果写成 Ubuntu 原生单测全绿。
  Ubuntu 路径另由真实启用、渲染、对账和会话检查验证；未新增测试文件。
- 11:53 重登后，Niri、Noctalia 与现有 Fcitx 均产生新进程，但 Ghostty 启动等待、
  Nautilus 首次打开为浅色。日志显示：11:53:02 注销期间 GTK portal 被旧主 portal
  再次激活，因显示连接失效退出；D-Bus 将该激活请求保留到 11:55:02 才超时。
  新会话中的 Ghostty 连续出现 25 秒 portal 等待，主 portal 也启动超时；11:55:10
  GTK 后端重新注册后恢复。当前 gsettings 为 `prefer-dark`、portal 值为 `uint32 1`。
  因此在 Niri `spawn-at-startup` 中增加 `systemctl --user --no-block start
  xdg-desktop-portal-gtk.service`：直接向服务管理器提交后端启动任务，解除遗留激活
  等待，不重启已运行的服务，也不改写 GTK 主题。Niri `--session` 在自启前完成
  显示环境导入，顺序依据 [Niri 26.04 启动源码](https://github.com/niri-wm/niri/blob/v26.04/src/main.rs#L197-L238)。
  修复经原子部署应用，6 个自定义/显示器/外观配置哈希不变，Niri 校验与 doctor
  通过。当前会话中独立 Ghostty 进程约 0.46 秒显示窗口，portal 暗色查询约 5 毫秒
  返回；这些结果不代替再次重登复验。该次备份位于
  `~/.local/state/nyxuri-compat-backups/20261025-120017-portal-login/`。
  12:03:35 再次登录后，GTK 后端、GNOME 后端与主 portal 均在 12:03:36 就绪，
  不再等待旧激活请求超时；用户确认 Ghostty 以及未经启动器预热、直接 Super+E
  打开的 Nautilus 均正常。Niri、Noctalia 与原有 Fcitx 配置产生的新进程正常运行，
  portal 返回暗色偏好，Fcitx IPC 返回激活状态。此结果验证本机的会话集成修复，
  不表示该竞态只会发生在 Ubuntu，也不覆盖 [Fcitx 新安装目标目录缺陷](../llms-wiki/ubuntu-compatibility.md#fcitx-配置路径限制)。
- 同次登录发现 `drkonqi-coredump-launcher` 持续报告自身崩溃，形成高频循环。
  已用 `systemctl --user mask --runtime --now drkonqi-coredump-launcher.socket
  drkonqi-coredump-launcher@.service` 临时阻断，未卸载或永久禁用 KDE 组件；运行时
  屏蔽通常持续至用户服务管理器退出或重启。恢复可执行对应的 `unmask --runtime`，
  再启动 socket，但报告器自身崩溃尚未修复，恢复后可能复发。此项为实机临时处置，
  未加入 Niri 的默认自启配置。

临时日志与截图在 `/tmp/nyxuri-niri-acceptance/`，不是持久交付目录。未提交或推送
本轮改动，未切换显示管理器，未迁移 Fcitx 的单元目标目录。

## 适配阶段的验证步骤（2026-10-25 补录）

从兼容指南迁入的操作参考，保留适配阶段的环境与验证边界，不表示新增验收结果。

### GI Cairo 转换器检查

可用 `python3 -c 'import gi; gi.require_foreign("cairo")'` 检查转换器，但该检查
不替代 Niri 中的窗口显示和指针定位验收。

### Plasma 中的验证方法

包查询、APT 安装模拟、语法检查、既有单元测试、临时 HOME 部署及 `niri validate`
不要求进入 Niri。禁止把临时 HOME 验证写入实际 `~/.config`，也不要为了验证切换
显示管理器、锁屏、启动第二套常驻 Shell 或覆盖 Plasma 的 portal 路由。

```bash
python3 -m compileall nyxuri tests
bash -n install.sh nyxuri/launcher.sh
shellcheck install.sh nyxuri/launcher.sh
niri validate --config units/niri/config.kdl
apt-get --simulate install niri noctalia python3-gi python3-cairo python3-gi-cairo gir1.2-gtklayershell-0.1
```

运行既有测试时还要隔离 `XDG_RUNTIME_DIR`，否则眼睛保护脚本可能尝试使用真实
会话的锁文件。QML 测试必须选择 Qt6 的 `qmltestrunner`；Ubuntu 上 `/usr/bin`
可能先找到 Qt5 的 qtchooser 包装器，可将 `/usr/lib/qt6/bin` 放在该次测试的 PATH 前端。

原有包管理测试按 Arch 命令形状编写，需要在 Arch 平台环境中执行；在 Ubuntu 上
运行测试时，对发行版探测进行显式覆盖只证明 Arch 分支的既有契约，不能冒充 Ubuntu
实机验收。包管理实际调用、配置校验与 Niri 登录后的验收必须分别记录。

### Niri 会话验收步骤

应在注销重登后检查首次应用启动和主题，
不能只检查已经恢复的会话。

Niri 中还需实际验证 Shell 动作、锁屏解锁、GTK/Qt/浏览器输入、通知、剪贴板、
portal 文件选择与屏幕共享，以及多显示器布局和自定义配置保留。自研 Shell 的预览
与切换方法见 [开发指南](../llms-wiki/shell/development.md)，可选功能缺口见
[Shell 已知问题](../shell/KNOWN-ISSUES.md)；静态配置校验和 IPC 就绪不代表这些功能全部可用。
