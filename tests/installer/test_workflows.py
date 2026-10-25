"""Ubuntu 安装流程契约：依赖门禁、部分完成和非交互默认选择。"""

import io
import unittest
from contextlib import redirect_stderr
from types import SimpleNamespace
from unittest.mock import patch

from tests.utils import TempEnv


class TestUbuntuInstallWorkflow(unittest.TestCase):
    def setUp(self):
        self.env = TempEnv()
        self.env.__enter__()
        self.addCleanup(self.env.__exit__, None, None, None)

    def _common(self, configs):
        """固定会话选择，让测试只观察依赖规划到部署的流程边界。"""
        from nyxuri.installer import workflows

        patches = [
            patch.object(workflows, "backend_available", return_value=True),
            patch.object(workflows, "current_platform", return_value="ubuntu"),
            patch("nyxuri.pkg.platform.current_platform", return_value="ubuntu"),
            patch.object(workflows, "discover_config_items", return_value=list(configs)),
            patch.object(workflows, "detect_preferred_wm", return_value="niri"),
            patch.object(workflows, "wallpapers_pack_present", return_value=True),
            patch.object(workflows, "_phase_preflight_check"),
            patch.object(workflows, "_enable_theme"),
            patch.object(workflows.transaction, "replay_enabled_hooks", return_value=[]),
            patch.object(workflows, "run_user_hooks", return_value=[]),
            patch.object(workflows, "render_completion_screen"),
            patch.object(workflows.transaction, "carry_baselines", return_value={}),
            patch.object(workflows.transaction, "resnapshot_units"),
        ]
        started = [p.start() for p in patches]
        self.addCleanup(lambda: [p.stop() for p in reversed(patches)])
        return workflows, started

    def test_unsupported_selected_unit_stops_before_sudo_or_deploy(self):
        """选择了无 Ubuntu 依赖映射的单元时，流程在认证与写配置前失败。"""
        workflows, started = self._common(["niri", "unsupported-unit"])
        preflight = started[6]
        load_unit = patch.object(workflows.registry, "load_unit", side_effect=lambda uid: SimpleNamespace(
            name=uid, is_optional=False, packages_repo=[], packages_aur=[], packages_flatpak=[],
            platforms={"ubuntu": {"packages": []}} if uid == "niri" else {
                "ubuntu": {"supported": False, "reason": "unsupported"}
            },
        ))
        load_unit.start()
        self.addCleanup(load_unit.stop)
        deploy = patch.object(workflows, "deploy_selected_configs")
        deploy_mock = deploy.start()
        self.addCleanup(deploy.stop)

        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps") as missing, \
             patch.object(workflows, "install_selected_deps") as install:
            result = workflows.install_configs_workflow("full")

        self.assertFalse(result)
        preflight.assert_not_called()
        missing.assert_not_called()
        install.assert_not_called()
        deploy_mock.assert_not_called()

    def test_unit_package_still_missing_after_install_stops_deployment(self):
        """所选单元的包经安装后仍缺失时，不进入配置复制阶段。"""
        workflows, _ = self._common(["niri"])
        deploy = patch.object(workflows, "deploy_selected_configs")
        deploy_mock = deploy.start()
        self.addCleanup(deploy.stop)

        installer = patch.object(workflows, "unit_package_installer", return_value=True)
        installer_mock = installer.start()
        self.addCleanup(installer.stop)
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps", return_value=[]), \
             patch.object(workflows.transaction, "missing_packages",
                          side_effect=[["niri"], ["niri"]]) as missing:
            result = workflows.install_configs_workflow("full")

        self.assertFalse(result)
        self.assertEqual(missing.call_count, 2)
        installer_mock.assert_called_once_with("niri", ["niri"])
        deploy_mock.assert_not_called()

    def test_unit_package_install_failure_stops_deployment(self):
        """所选单元依赖安装失败时，不继续复制配置。"""
        workflows, _ = self._common(["niri"])
        deploy = patch.object(workflows, "deploy_selected_configs")
        deploy_mock = deploy.start()
        self.addCleanup(deploy.stop)
        installer = patch.object(workflows, "unit_package_installer", return_value=False)
        installer_mock = installer.start()
        self.addCleanup(installer.stop)
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps", return_value=[]), \
             patch.object(workflows.transaction, "missing_packages", return_value=["niri"]):
            result = workflows.install_configs_workflow("full")

        self.assertFalse(result)
        installer_mock.assert_called_once_with("niri", ["niri"])
        deploy_mock.assert_not_called()

    def test_session_package_install_failure_stops_before_config_deploy(self):
        """工具链原生包失败后流程在配置部署前中止。"""
        workflows, _ = self._common(["niri"])
        deploy = patch.object(workflows, "deploy_selected_configs")
        deploy_mock = deploy.start()
        self.addCleanup(deploy.stop)
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps", side_effect=[["fish"], ["fish"]]), \
             patch.object(workflows, "install_selected_deps", return_value=False) as install:
            result = workflows.install_configs_workflow("full")

        self.assertFalse(result)
        install.assert_called_once_with(["fish"])
        deploy_mock.assert_not_called()

    def test_missing_manual_toolchain_resource_completes_config_but_returns_failure(self):
        """手动资源不可自动供应时可部署选中配置，但不能报告整装成功。"""
        workflows, _ = self._common(["niri"])
        incomplete = SimpleNamespace(
            supported=True, packages_repo=[], packages_aur=[], packages_flatpak=[],
            manual=["mpvpaper"],
        )
        deploy = patch.object(workflows, "deploy_selected_configs", return_value=[])
        deploy_mock = deploy.start()
        self.addCleanup(deploy.stop)
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps", side_effect=[["mpvpaper"], ["mpvpaper"]]), \
             patch.object(workflows, "install_selected_deps", return_value=False) as install, \
             patch.object(workflows, "core_requirements", return_value=incomplete), \
             patch.object(workflows.transaction, "missing_packages", return_value=[]), \
             patch.object(workflows, "_enable_wallpapers", return_value=True), \
             patch.object(workflows.transaction, "resnapshot_units"), \
             patch("builtins.print") as output, \
             redirect_stderr(io.StringIO()):
            result = workflows.install_configs_workflow("full")

        self.assertFalse(result)
        install.assert_called_once_with(["mpvpaper"])
        self.assertEqual(deploy_mock.call_args.kwargs["items_to_deploy"], ["niri"])
        rendered = " ".join(str(call.args[0]) for call in output.call_args_list)
        self.assertIn("mpvpaper", rendered)

    def test_config_mode_skips_all_package_checks(self):
        """install config 只部署所选蓝图，不检查或安装会话依赖。"""
        workflows, _ = self._common(["niri"])
        deploy = patch.object(workflows, "deploy_selected_configs", return_value=[])
        deploy_mock = deploy.start()
        self.addCleanup(deploy.stop)
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps") as deps, \
             patch.object(workflows, "unit_package_installer") as install, \
             patch.object(workflows.transaction, "missing_packages") as unit_deps:
            result = workflows.install_configs_workflow("config")

        self.assertTrue(result)
        self.assertEqual(deploy_mock.call_args.kwargs["items_to_deploy"], ["niri"])
        deps.assert_not_called()
        install.assert_not_called()
        unit_deps.assert_not_called()

    def test_full_install_supplies_core_then_unit_packages_before_configs(self):
        """完整安装先供给会话工具链，再供给单元包，最后部署配置且不启用单元。"""
        workflows, _ = self._common(["niri"])
        events = []
        deploy = patch.object(
            workflows, "deploy_selected_configs",
            side_effect=lambda **kwargs: events.append(("configs", kwargs["items_to_deploy"])) or [],
        )
        deploy_mock = deploy.start()
        self.addCleanup(deploy.stop)

        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps", return_value=["fish"]), \
             patch.object(workflows, "install_selected_deps",
                          side_effect=lambda names: events.append(("core", names)) or True), \
             patch.object(workflows.transaction, "missing_packages",
                          side_effect=[["niri"], []]) as missing, \
             patch.object(workflows, "unit_package_installer",
                          side_effect=lambda uid, names: events.append(("unit", uid, names)) or True), \
             patch.object(workflows.transaction, "unit_on") as unit_on:
            result = workflows.install_configs_workflow("full")

        self.assertTrue(result)
        self.assertEqual(events, [
            ("core", ["fish"]),
            ("unit", "niri", ["niri"]),
            ("configs", ["niri"]),
        ])
        self.assertEqual(missing.call_count, 2)
        deploy_mock.assert_called_once()
        unit_on.assert_not_called()

    def test_noninteractive_full_install_skips_uninstalled_optional_unit(self):
        """Ubuntu 非交互整装默认排除未安装的 Greeter，也不启用任何单元。"""
        workflows, _ = self._common(["niri", "greeter"])
        deploy = patch.object(workflows, "deploy_selected_configs", return_value=[])
        deploy_mock = deploy.start()
        self.addCleanup(deploy.stop)
        supply = patch.object(workflows, "supply_installed", return_value=False)
        supply_mock = supply.start()
        self.addCleanup(supply.stop)
        with patch("sys.stdin.isatty", return_value=False), \
             patch.object(workflows, "get_missing_deps", return_value=[]), \
             patch.object(workflows.transaction, "missing_packages", return_value=[]), \
             patch.object(workflows, "unit_package_installer") as install, \
             patch.object(workflows.transaction, "unit_on") as unit_on:
            result = workflows.install_configs_workflow("full")

        self.assertTrue(result)
        supply_mock.assert_called_once()
        self.assertEqual(supply_mock.call_args.args[0].name, "greeter")
        self.assertEqual(deploy_mock.call_args.kwargs["items_to_deploy"], ["niri"])
        install.assert_not_called()
        unit_on.assert_not_called()


if __name__ == "__main__":
    unittest.main()
