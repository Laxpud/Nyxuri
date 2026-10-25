# Ubuntu 兼容与验收

> 本页说明 Ubuntu 的依赖供应、安装边界与验证方法，以 `nyxuri/pkg/`、单元 manifest 和当前软件源查询结果为准；剩余验收只在 [ROADMAP](../ROADMAP.md#ubuntu-兼容) 维护。

## 支持边界

当前适配基线为 Ubuntu 26.04，源码入口沿用 `nyxuri/launcher.sh`，Python 需 3.11+。
其他 Ubuntu 版本或衍生发行版可以识别为 Ubuntu 后端，但不代表其软件源、运行时版本
和桌面行为已经验收。原有 Arch/CachyOS 依赖及 AUR 打包声明继续保留。

- 包管理后端读取 `/etc/os-release`，Ubuntu 使用 `apt-get`、`apt-cache` 和
  `dpkg-query`，不根据 PATH 里偶然出现的 `pacman` 判断发行版。
- 安装前检查已安装状态与当前软件源候选；不自动添加 PPA、导入密钥、刷新索引、
  执行外部安装脚本或编译源码。源索引不可用时先提示用户准备软件源。
- `nyxuri pkg upgrade` 在 Ubuntu 执行普通 APT 升级；`remove` 保留配置，
  不附带 `autoremove`、`purge` 或发行版升级。
- `on <unit>`、CLI/工坊详情、依赖菜单和应用菜单共用平台依赖解析。
  没有 Ubuntu 声明的原生包不会退回 Arch 包名；手动依赖不会作为 APT 包名执行。
- `off` 仍只停用配置并保留软件包，原子部署、Dunder、Vault 和快照契约不变。

## 安装方式

在已准备源码的目录中使用仓库自身入口，避免命中旧版本用户级启动器：

```bash
bash nyxuri/launcher.sh list niri
bash nyxuri/launcher.sh pkg search repo kitty
bash nyxuri/launcher.sh pkg info kitty
bash nyxuri/launcher.sh on kitty
```

单元启用会先披露缺失依赖；来源未配置或手动资源缺失时，报告原因，不把单元记为成功启用。
依赖齐全但会话钩子失败时，沿用单元事务的非致命警告契约：配置可以启用，CLI 显示
`Hook incomplete`。这不代表 Noctalia 的 GTK 渲染等会话动作已经完成。
手动安装了兼容二进制或资源后，再次启用会重新检测，不需要伪造 dpkg 状态。

`install config` 只部署配置，仍要求用户自行准备运行时。`install full` 在 Ubuntu
安装会话工具链与所选单元依赖，非交互默认不安装未使用的可选应用或 greeter。
会话工具链中的手动资源缺失时，普通包与配置可以完成，命令会报告未完成并返回非零；
普通软件包安装失败或所选单元依赖缺失会中止后续部署。配置部署不会替用户启用新单元。

完整桌面必须另行核对 Niri、Noctalia 和 portal 运行情况。Noctalia v5 与旧版基于
Quickshell 的 Noctalia Shell 是不同运行时；Nyxuri 自研 Shell 仍需单独的 Quickshell。

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

## Plasma 中的验证方法

包查询、APT 安装模拟、语法检查、既有单元测试、临时 HOME 部署及 `niri validate`
不要求进入 Niri。禁止把临时 HOME 验证写入实际 `~/.config`，也不要为了验证切换
显示管理器、锁屏、启动第二套常驻 Shell 或覆盖 Plasma 的 portal 路由。

```bash
python3 -m compileall nyxuri tests
bash -n install.sh nyxuri/launcher.sh
shellcheck install.sh nyxuri/launcher.sh
niri validate --config units/niri/config.kdl
apt-get --simulate install niri noctalia python3-gi python3-cairo gir1.2-gtklayershell-0.1
```

运行既有测试时还要隔离 `XDG_RUNTIME_DIR`，否则眼睛保护脚本可能尝试使用真实
会话的锁文件。QML 测试必须选择 Qt6 的 `qmltestrunner`；Ubuntu 上 `/usr/bin`
可能先找到 Qt5 的 qtchooser 包装器，可将 `/usr/lib/qt6/bin` 放在该次测试的 PATH 前端。

原有包管理测试按 Arch 命令形状编写，需要在 Arch 平台环境中执行；在 Ubuntu 上
运行测试时，对发行版探测进行显式覆盖只证明 Arch 分支的既有契约，不能冒充 Ubuntu
实机验收。包管理实际调用、配置校验与 Niri 登录后的验收必须分别记录。

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

## 已确认的原有 Fcitx 路径问题

`fcitx5-rime` 当前默认生活区是 `$XDG_CONFIG_HOME/fcitx5-rime`，而 Fcitx 读取
`$XDG_CONFIG_HOME/fcitx5`。单元 hook 只管理用户数据目录中的皮肤与 Rime 方案，
不会把 `profile` / `conf/classicui.conf` 转移到 Fcitx 配置目录。因此，依赖检测通过
不代表输入法配置生效；本轮不能把完整 Fcitx 生命周期验收记为通过。

这是原有单元目标路径缺陷。改成共享目录需要一起处理单元分类与已有 ledger 的迁移，
不能直接改 target 后执行 off：旧快照中的相对文件名可能对应新目录里的用户文件。
2026-10-25 用户确认保留原契约，本轮只记录已知问题，不修改目标路径、单元分类、
旧启用记录或既有测试断言。未来若单独修复，需要先设计旧布局识别和迁移，再处理共享
目录中的文件归属；不能把本轮的 Ubuntu 依赖适配当作迁移已经完成。

## 数据声明与维护

平台字段含义以 [manifest-schema](manifest-schema.md#平台依赖覆盖) 为准。
`ModuleManifest` 与 `CatalogEntry` 的原始包字段始终保留 Arch 声明；只有运行时消费者
调用 `resolve_requirements()` 选择本机平台。`packaging/gen-deps.py` 继续读取原始字段，
在 Ubuntu 上生成 AUR 元数据也不能混入 Debian 包名。
