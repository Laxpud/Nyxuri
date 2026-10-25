# Ubuntu 兼容

> 本页说明 Ubuntu 的依赖供应、安装边界与会话限制，以 `nyxuri/pkg/`、单元 manifest 和 `catalog.toml` 为准；进度只在 [ROADMAP](../ROADMAP.md#ubuntu-兼容) 维护。

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

Noctalia v5 与旧版基于 Quickshell 的 Noctalia Shell 是不同运行时；Nyxuri 自研
Shell 仍需单独的 Quickshell。

Noctalia 单元附带的 Orbit 使用 GTK3 的 `draw` 信号绘制 Cairo 内容。Ubuntu 将
绘图模块 `python3-cairo` 与 GI 的 Cairo 转换器 `python3-gi-cairo` 分包；两者都需
声明，单独安装 `python3-gi` 和 `python3-cairo` 不保证 GTK 绘图回调可用。

Ubuntu 上除 Quickshell 外，还需安装 Nyxuri Shell 使用的 QML 模块；具体依赖见
[catalog.toml](../catalog.toml) 的 Quickshell Ubuntu 条目。Qt 共享库不能代替 QML 插件。

Nyxuri Shell 的图标要求 `Material Symbols Rounded` 与 `Material Symbols Outlined`
两个字族，旧 `Material Icons` 不能替代。字体需手动准备并能被 Fontconfig 识别；
依赖流程只检测，不下载或安装字体。可使用 Google 提供的预编译 TTF：
[Rounded](https://github.com/google/material-design-icons/blob/master/variablefont/MaterialSymbolsRounded%5BFILL%2CGRAD%2Copsz%2Cwght%5D.ttf)、
[Outlined](https://github.com/google/material-design-icons/blob/master/variablefont/MaterialSymbolsOutlined%5BFILL%2CGRAD%2Copsz%2Cwght%5D.ttf)。

## 依赖供应

包名、手动资源与平台支持声明以单元 manifest 和 [catalog.toml](../catalog.toml)
为准，不以某台机器的软件源状态推断其他安装环境。安装前使用 `pkg info` 或
`apt-cache policy` 检查当前源和缓存中的候选；无候选时先准备来源，再执行安装。

- Niri、Noctalia、Quickshell 等声明了额外 APT 来源要求的软件，需要预先配置兼容来源；
  Nyxuri 不自动添加来源或导入密钥。
- 手动二进制依赖安装后应能由对应命令探针发现；字体与 Rime 等资源按资源探针检查。
  `mpvpaper` 声明为手动依赖，缺失时视频壁纸不可用，不影响静态壁纸文件部署。
- Flatpak 应用使用目录中声明的 app ID，不转换为原生包名。
- Mango 和 Shelly 当前未声明 Ubuntu 支持；不要套用 Arch 安装或构建流程。
- Greeter 服务与显示管理器切换应单独安排，不属于普通依赖安装。

## Niri 会话行为与限制

Niri 配置在登录时显式启动 GTK portal。该后端提供暗色偏好等接口；退出会话时遗留的
D-Bus 激活等待可能使新会话中的 GTK 应用启动缓慢或首次主题不正确。
`niri --session` 导入显示环境后，`spawn-at-startup` 向 systemd 提交后端启动任务，
不阻塞 Shell，也不重启已运行的服务。

自研 Shell 的可选功能限制见 [Shell 已知问题](../shell/KNOWN-ISSUES.md)。

Niri 26.04 的 portal 全屏截图接口只接受单输出，双屏会失败；可使用普通 Niri
单屏截图路径。限制依据 [Niri 26.04 源码](https://github.com/niri-wm/niri/blob/v26.04/src/niri.rs#L5298-L5310)，
不能据此推断其他版本或所有截图接口都存在同样限制。

## Fcitx 配置路径限制

`fcitx5-rime` 当前默认生活区是 `$XDG_CONFIG_HOME/fcitx5-rime`，而 Fcitx 读取
`$XDG_CONFIG_HOME/fcitx5`。单元 hook 只管理用户数据目录中的皮肤与 Rime 方案，
不会把 `profile` / `conf/classicui.conf` 转移到 Fcitx 配置目录。因此，依赖检测通过
不代表输入法配置生效；已有 Fcitx 配置可用，也不能证明新安装路径正确。

这是原有单元目标路径缺陷。改成共享目录需要一起处理单元分类与已有 ledger 的迁移，
不能直接改 target 后执行 off：旧快照中的相对文件名可能对应新目录里的用户文件。
修复需要先设计旧布局识别和账本迁移，再处理共享目录中的文件归属；
Ubuntu 依赖适配不包含这项迁移。

## 数据声明与维护

平台字段含义以 [manifest-schema](manifest-schema.md#平台依赖覆盖) 为准。
`ModuleManifest` 与 `CatalogEntry` 的原始包字段始终保留 Arch 声明；只有运行时消费者
调用 `resolve_requirements()` 选择本机平台。`packaging/gen-deps.py` 继续读取原始字段，
在 Ubuntu 上生成 AUR 元数据也不能混入 Debian 包名。
