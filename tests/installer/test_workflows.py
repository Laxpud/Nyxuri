"""安装流程契约：依赖门禁、账本事务和非交互候选范围。"""

import io
import unittest
from contextlib import redirect_stderr
from types import SimpleNamespace
from unittest.mock import patch

from tests.utils import TempEnv


class TestUbuntuInstallWorkflow(unittest.TestCase):
    def setUp(self):
        self.ctx = TempEnv()
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

    def _common(self, configs):
        """隔离会话探测和钩子，观察供应检查到单元事务的实际调用。"""
        from nyxuri.installer import workflows
        from nyxuri.kernel.transaction import Step

        targets = {
            "backend": patch.object(workflows, "backend_available", return_value=True),
            "platform": patch.object(workflows, "current_platform", return_value="ubuntu"),
            "requirements_platform": patch("nyxuri.pkg.platform.current_platform", return_value="ubuntu"),
            "items": patch.object(workflows, "discover_config_items", return_value=list(configs)),
            "wm": patch.object(workflows, "detect_preferred_wm", return_value="niri"),
            "wallpapers": patch.object(workflows, "wallpapers_pack_present", return_value=True),
            "preflight": patch.object(workflows, "_phase_preflight_check"),
            "hooks": patch.object(workflows, "run_user_hooks", return_value=[]),
            "screen": patch.object(workflows, "render_completion_screen"),
            "plan": patch.object(workflows.transaction, "plan_on", side_effect=lambda uid: [uid]),
            "conflicts": patch("nyxuri.tui.choose_conflict_policy", return_value=False),
            "on": patch.object(workflows.transaction, "unit_on",
                               side_effect=lambda uid, **kwargs: [Step(uid, True, "enabled")]),
        }
        mocks = {key: target.start() for key, target in targets.items()}
        self.addCleanup(lambda: [target.stop() for target in reversed(list(targets.values()))])
        return workflows, mocks

    def test_unsupported_selected_unit_stops_before_sudo_or_deploy(self):
        """无 Ubuntu 映射的单元在认证、供应和文件事务之前失败。"""
        workflows, mocks = self._common(["niri", "unsupported-unit"])
        with patch.object(workflows.registry, "load_unit", side_effect=lambda uid: SimpleNamespace(
            name=uid, is_optional=False, packages_repo=[], packages_aur=[], packages_flatpak=[],
            platforms={"ubuntu": {"packages": []}} if uid == "niri" else {
                "ubuntu": {"supported": False, "reason": "unsupported"}})), \
             patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps") as missing, \
             patch.object(workflows, "install_selected_deps") as install:
            self.assertFalse(workflows.install_configs_workflow("full"))
        mocks["preflight"].assert_not_called()
        missing.assert_not_called()
        install.assert_not_called()
        mocks["on"].assert_not_called()

    def test_conflict_cancel_stops_before_auth_packages_and_file_writes(self):
        """冲突界面取消发生在 sudo 和依赖供应之前，不留下配置或账本。"""
        from nyxuri.kernel import ledger
        workflows, mocks = self._common(["niri"])
        mocks["conflicts"].return_value = None
        with patch("sys.stdin.isatty", return_value=True), \
             patch.object(workflows, "run_master_component_menu", return_value={
                 "configs": ["niri"], "wallpapers": False, "backup": False}), \
             patch.object(workflows, "get_missing_deps") as missing, \
             patch.object(workflows, "install_selected_deps") as install:
            self.assertFalse(workflows.install_configs_workflow("full"))
        mocks["preflight"].assert_not_called()
        mocks["on"].assert_not_called()
        missing.assert_not_called()
        install.assert_not_called()
        self.assertFalse(ledger.ledger_path().exists())

    def test_unit_package_still_missing_after_install_stops_deployment(self):
        """包安装回调成功但再次探测仍缺包时，不进入文件事务。"""
        workflows, mocks = self._common(["niri"])
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps", return_value=[]), \
             patch.object(workflows, "unit_package_installer", return_value=True) as installer, \
             patch.object(workflows.transaction, "missing_packages", side_effect=[["niri"], ["niri"]]) as missing:
            self.assertFalse(workflows.install_configs_workflow("full"))
        self.assertEqual(missing.call_count, 2)
        installer.assert_called_once_with("niri", ["niri"])
        mocks["on"].assert_not_called()

    def test_unit_package_install_failure_stops_deployment(self):
        """所选单元依赖供给失败时，不继续复制配置。"""
        workflows, mocks = self._common(["niri"])
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps", return_value=[]), \
             patch.object(workflows, "unit_package_installer", return_value=False) as installer, \
             patch.object(workflows.transaction, "missing_packages", return_value=["niri"]):
            self.assertFalse(workflows.install_configs_workflow("full"))
        installer.assert_called_once_with("niri", ["niri"])
        mocks["on"].assert_not_called()

    def test_session_package_install_failure_stops_before_config_deploy(self):
        """工具链包失败时，在单元配置事务前停止。"""
        workflows, mocks = self._common(["niri"])
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps", side_effect=[["fish"], ["fish"]]), \
             patch.object(workflows, "install_selected_deps", return_value=False) as install:
            self.assertFalse(workflows.install_configs_workflow("full"))
        install.assert_called_once_with(["fish"])
        mocks["on"].assert_not_called()

    def test_missing_manual_toolchain_resource_stops_before_config_deploy(self):
        """工具链手动资源尚未供应时，不把复制配置当作完整安装成功。"""
        workflows, mocks = self._common(["niri"])
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps", side_effect=[["mpvpaper"], ["mpvpaper"]]), \
             patch.object(workflows, "install_selected_deps", return_value=False) as install, \
             redirect_stderr(io.StringIO()) as error:
            self.assertFalse(workflows.install_configs_workflow("full"))
        install.assert_called_once_with(["mpvpaper"])
        mocks["on"].assert_not_called()
        self.assertIn("mpvpaper", error.getvalue())

    def test_config_mode_skips_packages_and_hooks_but_uses_unit_transaction(self):
        """配置模式仍登记归属，并明确将运行时激活保留为未完成阶段。"""
        workflows, mocks = self._common(["niri"])
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps") as deps, \
             patch.object(workflows, "unit_package_installer") as install, \
             patch.object(workflows.transaction, "missing_packages") as unit_deps:
            self.assertTrue(workflows.install_configs_workflow("config"))
        mocks["on"].assert_called_once_with("niri", force=False, install_packages=None,
                                           run_hooks=False, check_packages=False)
        deps.assert_not_called()
        install.assert_not_called()
        unit_deps.assert_not_called()
        mocks["hooks"].assert_not_called()

    def test_full_install_supplies_core_then_unit_packages_before_unit_transaction(self):
        """整装按核心供应、单元供应、部署登记顺序调用统一事务。"""
        workflows, mocks = self._common(["niri"])
        from nyxuri.kernel.transaction import Step
        events = []
        mocks["on"].side_effect = lambda uid, **kwargs: events.append(("on", uid)) or [Step(uid, True, "enabled")]
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps", return_value=["fish"]), \
             patch.object(workflows, "install_selected_deps",
                          side_effect=lambda names: events.append(("core", names)) or True), \
             patch.object(workflows.transaction, "missing_packages", side_effect=[["niri"], []]) as missing, \
             patch.object(workflows, "unit_package_installer",
                          side_effect=lambda uid, names: events.append(("unit", uid, names)) or True) as installer:
            self.assertTrue(workflows.install_configs_workflow("full"))
        self.assertEqual(events, [("core", ["fish"]), ("unit", "niri", ["niri"]), ("on", "niri")])
        self.assertEqual(missing.call_count, 2)
        mocks["on"].assert_called_once_with("niri", force=False, install_packages=installer,
                                           run_hooks=True, check_packages=True)
        mocks["hooks"].assert_called_once()

    def test_noninteractive_full_install_skips_uninstalled_optional_unit(self):
        """Ubuntu 非交互整装只启用已选常规单元，不顺带安装可选 Greeter。"""
        workflows, mocks = self._common(["niri", "greeter"])
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "supply_installed", return_value=False) as supply, \
             patch.object(workflows, "get_missing_deps", return_value=[]), \
             patch.object(workflows.transaction, "missing_packages", return_value=[]), \
             patch.object(workflows, "unit_package_installer") as install:
            self.assertTrue(workflows.install_configs_workflow("full"))
        supply.assert_called_once()
        self.assertEqual(supply.call_args.args[0].name, "greeter")
        install.assert_not_called()
        self.assertEqual([call.args[0] for call in mocks["on"].call_args_list], ["niri"])

    def test_successful_install_registers_actual_content_for_doctor(self):
        """从空 HOME 经真实单元事务安装，文件和账本必须能直接完成对账。"""
        from nyxuri.installer import workflows
        from nyxuri.kernel import ledger, transaction
        units = self.ctx.home / "isolated-units"
        source = units / "install-example"
        source.mkdir(parents=True)
        (source / "manifest.toml").write_text(
            'packages = []\n[platforms.ubuntu]\npackages = []\n', encoding="utf-8")
        (source / "config").write_text("payload", encoding="utf-8")
        self.ctx.env.units_src = units
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "backend_available", return_value=True), \
             patch.object(workflows, "current_platform", return_value="ubuntu"), \
             patch("nyxuri.pkg.platform.current_platform", return_value="ubuntu"), \
             patch.object(workflows, "discover_config_items", return_value=["install-example"]), \
             patch.object(workflows, "wallpapers_pack_present", return_value=True), \
             patch.object(workflows, "_phase_preflight_check"), \
             patch.object(workflows, "get_missing_deps", return_value=[]), \
             patch.object(workflows, "run_user_hooks", return_value=[]), \
             patch.object(workflows, "render_completion_screen"), \
             patch("builtins.print"):
            self.assertTrue(workflows.install_configs_workflow("full"))
        self.assertEqual((self.ctx.env.config_dir / "install-example/config").read_text(), "payload")
        self.assertEqual(ledger.get_unit("install-example")["state"], "enabled")
        self.assertEqual(transaction.audit_units("install-example"), {"install-example": "Synced"})


if __name__ == "__main__":
    unittest.main()
