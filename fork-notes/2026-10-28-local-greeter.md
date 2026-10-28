# 本机 Greeter 安装与 SDDM 恢复

> 记录日期：2026-10-28。适用于本机 Ubuntu 26.04 / Niri；这是本次切换与恢复记录，不是通用安装指南。

## 切换前

- 当前显示管理器：SDDM，服务 active / enabled。
- `/etc/systemd/system/display-manager.service` 指向 `/usr/lib/systemd/system/sddm.service`。
- `/etc/X11/default-display-manager` 为 `/usr/bin/sddm`。
- `greetd` 与 `noctalia-greeter` 尚未安装；本次安装使用现有 APT 来源。
- 只切换下次启动使用的显示管理器，不停止当前 SDDM，不自动注销或重启。

## 安装与验证状态

- 安装前备份：`/var/backups/nyxuri-greeter-20261028-hUQElL/`，目录仅 root 可读；
  保存了原显示管理器软链接及 `/etc/X11/default-display-manager`，原先不存在的路径不伪造备份。
- 通过当前仓库的 `nyxuri on greeter` 完成，退出码 0。安装 `greetd 0.10.3-5`、
  `noctalia-greeter 1.7.0-2~bpo26.04.1` 及三个运行库，没有升级或移除现有软件。
- `display-manager.service` 已指向 greetd；greetd 为 enabled / inactive，SDDM 为
  disabled / active，当前桌面保持运行。原显示管理器记录为 `sddm`，
  `/etc/X11/default-display-manager` 仍为 `/usr/bin/sddm`。
- `doctor greeter` 为 `Synced`，包内用户、配置路径与 systemd 实际命令检查通过。
- 本机 `noctalia --version` 为 v5.3.0；虽然命令帮助列出 `greeter-sync`，当前运行实例
  对 `noctalia msg greeter-sync` 返回 `unknown command`，未生成 `sync.toml`。
  本次未同步壁纸与配色，不把请求失败记为完成；先使用 Greeter 默认外观，重启后另行核对。
- 用户随后重启并确认看到 Noctalia Greeter；11:37 的 greetd 日志确认登录并启动 Niri。
- 重启前后 Noctalia 均为 v5.3.0。09:48 启动时 Greeter 尚未安装，日志明确记录
  `greeter-sync` 未注册；重启后手动同步成功，11:43 的 Noctalia 日志记录
  `synced shell appearance to greeter`，辅助程序也明确报告写入状态目录且退出码为 0。
  自动同步开关为 true；尚未再次退出会话目视验收同步后的登录外观。

## Kitty 主题连带变化

- 11:13:30 启用 Greeter 时，公共消费者刷新清空了 Noctalia 的 Kitty/Qt 内置模板选择。
  内置撤回脚本移除 `kitty.conf` 中的主题 include 与 `themes/noctalia.conf`，并重载 Kitty。
- 替代的 `~/.config/nyxuri/templates/kitty.conf`、`qtct.conf` 尚未部署，日志同时报告
  输入不存在，导致 Kitty 丢失原配色。这是 Nyxuri 刷新范围与旧配置迁移的问题。
- 修复让无关单元只更新门控；保留已有原生模板，避免双重生产者；新模板输入必须可读。
  既有测试只调整平台夹具、模板前置条件和 manifest 期望，没有新增测试用例。
- 恢复前完整快照：`~/.config/nyxuri/backups/snapshot_20261028_121451_657245/`。
  通过 `unit_refresh("theme")` 正常部署缺失模板，再由 Noctalia `templates-apply` 生成
  Kitty/Qt 实际色板。用户确认主配置已保存并退出编辑器后，将主题 include 补回
  `kitty.conf` 的个人配置引用之前；`__custom__.conf` 原内容保持不变。
- Kitty 实际配置解析确认：字体仍为 `Maple Mono NF CN`，背景 `#131315`、前景
  `#e5e1e3`，与当前 Noctalia 配色一致；已向现有 Kitty 实例发送重载信号。
  原有 `ctrl+scroll_up/down` 鼠标绑定仍被 Kitty 报为无效，未顺带改动。
- 本次相关现有检查 227 项通过，CLI/文档检查 68 项通过；未运行全量回归。

## 正常恢复 SDDM

在桌面终端或文本控制台，以普通用户运行：

```bash
env -u XDG_CONFIG_HOME -u XDG_CACHE_HOME -u XDG_DATA_HOME -u XDG_STATE_HOME \
  bash /home/laxpud/src/Nyxuri/nyxuri/launcher.sh off greeter
```

确认提示已恢复 SDDM 后，保存工作再重启。此命令保留软件包和 Greeter 外观数据，
撤回 Nyxuri 外观授权；不会立即停止当前桌面。

## 登录界面无法使用时

按 `Ctrl+Alt+F3`（必要时 F2/F4）进入文本控制台，用本机用户名和密码登录，先执行上面的恢复命令。
若 Nyxuri 命令不可用或报告恢复失败，可直接恢复下次启动的登录管理器：

```bash
sudo systemctl disable greetd
sudo systemctl enable --force sddm
readlink -f /etc/systemd/system/display-manager.service
cat /etc/X11/default-display-manager
```

第一项输出应指向 `sddm.service`，第二项应是 `/usr/bin/sddm`。如果第二项被改成其他值，恢复为：

```bash
printf '%s\n' /usr/bin/sddm | sudo tee /etc/X11/default-display-manager
```

确认已保存工作后执行 `sudo reboot`。直接用 systemctl 应急恢复不会同步 Nyxuri 账本，
回到桌面后再运行 `off greeter` 完成单元清理。不要在仍有未保存工作的会话中使用
`systemctl stop/restart sddm` 或 `--now`。
