"""验证 GTK 渲染钩子的真实返回值与 IPC 顺序，避免复制配置被当成渲染成功。"""

import contextlib
import io
import hashlib
import json
import shutil
import tomllib
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import call, patch

from tests.utils import TempEnv


class TestNoctaliaRenderHook(unittest.TestCase):
    def setUp(self):
        self.ctx = TempEnv()
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)
        hook = Path(__file__).resolve().parents[2] / "units/noctalia/hooks/render-gtk"
        # 加载交付脚本本身；只替换外部进程边界，不重写钩子的成功/失败逻辑。
        self.main = runpy.run_path(str(hook))["main"]

    def invoke(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = self.main()
        return status, output.getvalue()

    @staticmethod
    def expected_calls():
        return [
            call(["noctalia", "msg", "config-reload"], timeout=15, check=False,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
            call(["noctalia", "msg", "templates-apply"], timeout=30, check=False,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
        ]

    def test_missing_executable_is_pending_without_ipc(self):
        with patch("shutil.which", return_value=None), patch("subprocess.run") as runner:
            status, output = self.invoke()
        self.assertEqual(status, 1)
        self.assertIn("pending", output)
        runner.assert_not_called()

    def test_reload_failure_stops_before_template_application(self):
        with patch("shutil.which", return_value="/fixture/noctalia"), \
             patch("subprocess.run", return_value=subprocess.CompletedProcess([], 7)) as runner:
            status, output = self.invoke()
        self.assertEqual(status, 1)
        self.assertIn("remain pending", output)
        self.assertEqual(runner.call_args_list, self.expected_calls()[:1])

    def test_template_failure_is_not_reported_as_rendered(self):
        with patch("shutil.which", return_value="/fixture/noctalia"), \
             patch("subprocess.run", side_effect=[
                 subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 1),
             ]) as runner:
            status, output = self.invoke()
        self.assertEqual(status, 1)
        self.assertNotIn("templates rendered", output)
        self.assertEqual(runner.call_args_list, self.expected_calls())

    def test_timeout_or_os_error_is_pending_at_either_stage(self):
        for error in (OSError("unavailable"), subprocess.TimeoutExpired("noctalia", 15)):
            for stage in (0, 1):
                with self.subTest(error=type(error).__name__, stage=stage), \
                     patch("shutil.which", return_value="/fixture/noctalia"), \
                     patch("subprocess.run", side_effect=[
                         *[subprocess.CompletedProcess([], 0) for _ in range(stage)], error,
                     ]) as runner:
                    status, output = self.invoke()
                self.assertEqual(status, 1)
                self.assertIn("retry", output)
                self.assertEqual(runner.call_args_list, self.expected_calls()[:stage + 1])

    def test_success_requires_reload_then_apply(self):
        with patch("shutil.which", return_value="/fixture/noctalia"), \
             patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)) as runner:
            status, output = self.invoke()
        self.assertEqual(status, 0)
        self.assertIn("templates rendered", output)
        self.assertEqual(runner.call_args_list, self.expected_calls())


class TestExternalOutputLifecycle(unittest.TestCase):
    """验证已批准的跨目录原值恢复、个人修改及停用后渲染场景。"""

    def setUp(self):
        self.ctx = TempEnv()
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)
        from nyxuri.desktop import owned_outputs
        self.outputs = owned_outputs

    def enable(self, unit_id):
        from nyxuri.kernel import ledger
        config = self.ctx.env.config_dir / "noctalia/noctalia-config.toml"
        files = ({"noctalia-config.toml": hashlib.sha256(config.read_bytes()).hexdigest()}
                 if unit_id == "noctalia" and config.is_file() else {})
        ledger.set_unit(unit_id, state="enabled", files=files)

    def test_restore_original_and_preserve_later_user_changes(self):
        css = self.ctx.home / ".config/gtk-3.0/gtk.css"
        css.parent.mkdir(parents=True)
        css.write_bytes(b"personal original")
        self.assertFalse(self.outputs.write_output("noctalia", "theme", css, b"rendered"))
        self.assertEqual(css.read_bytes(), b"personal original")
        self.assertTrue(self.outputs.write_output("noctalia", "theme", css, b"rendered", force=True))
        self.outputs.withdraw_outputs(producer="noctalia")
        self.assertEqual(css.read_bytes(), b"personal original")
        self.outputs.write_output("noctalia", "theme", css, b"rendered", force=True)
        css.write_bytes(b"later personal edit")
        self.assertFalse(self.outputs.write_output("noctalia", "theme", css, b"new colors"))
        self.outputs.withdraw_outputs(producer="noctalia")
        self.assertEqual(css.read_bytes(), b"later personal edit")

    def test_force_authorization_is_identity_bound_and_consumed_once(self):
        from nyxuri.state.backup import backup_configs
        css = self.ctx.env.config_dir / "gtk-3.0/gtk.css"
        css.parent.mkdir()
        css.write_bytes(b"unknown theme")
        with contextlib.redirect_stdout(io.StringIO()):
            backup = backup_configs(note="force-output-fixture", interactive=False)
        self.outputs.authorize_output_overwrites("theme", backup)
        css.write_bytes(b"changed after approval")
        self.assertFalse(self.outputs.write_output("noctalia", "theme", css, b"rendered"))
        self.assertEqual(css.read_bytes(), b"changed after approval")
        self.outputs.authorize_output_overwrites("theme", backup)
        self.assertTrue(self.outputs.write_output("noctalia", "theme", css, b"rendered"))
        css.write_bytes(b"later change")
        self.assertFalse(self.outputs.write_output("noctalia", "theme", css, b"new render"))
        self.assertEqual(css.read_bytes(), b"later change")

    def test_daemon_commit_protects_unknown_output_until_snapshot_authorization(self):
        from nyxuri.state.backup import backup_configs
        for uid in ("noctalia", "theme"):
            self.enable(uid)
        css = self.ctx.env.config_dir / "gtk-3.0/gtk.css"
        css.parent.mkdir()
        css.write_bytes(b"existing personal CSS")
        stage = self.ctx.env.state_dir / "template-staging/noctalia/nyxuri_gtk3"
        stage.parent.mkdir(parents=True)
        stage.write_bytes(b"rendered colors")
        self.assertFalse(self.outputs.commit_template("nyxuri_gtk3"))
        self.assertEqual(css.read_bytes(), b"existing personal CSS")
        with contextlib.redirect_stdout(io.StringIO()):
            backup = backup_configs(note="daemon-force-fixture", interactive=False)
        captured = json.loads((backup / "external/outputs.json").read_text())
        self.assertIn(str(css), captured["unmanaged_targets"])
        self.outputs.authorize_output_overwrites("theme", backup)
        self.assertTrue(self.outputs.commit_template("nyxuri_gtk3"))
        self.assertEqual(css.read_bytes(), b"rendered colors")
        self.outputs.restore_state(backup / "external", {"version": 1, "file": "outputs.json"})
        self.assertEqual(css.read_bytes(), b"existing personal CSS")

    def test_unknown_equal_output_can_be_registered_without_being_removed(self):
        target = self.ctx.env.config_dir / "gtk-3.0/gtk.css"
        target.parent.mkdir()
        target.write_bytes(b"same output")
        self.assertTrue(self.outputs.write_output("noctalia", "theme", target, b"same output"))
        self.outputs.withdraw_outputs(producer="noctalia")
        self.assertEqual(target.read_bytes(), b"same output")

    def test_personal_noctalia_template_config_is_not_rewritten_by_other_unit(self):
        config = self.ctx.env.config_dir / "noctalia/noctalia-config.toml"
        config.parent.mkdir()
        config.write_text('[theme.templates]\nbuiltin_ids = ["kitty"]\n')
        self.enable("noctalia")
        self.enable("theme")
        # 基线登记后发生个人修改，消费者开关只能改外置门控。
        config.write_text('[theme.templates]\nbuiltin_ids = ["kitty", "custom"]\n')
        original = config.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "configuration conflict"):
            self.outputs.refresh_consumer_outputs({"kitty": True})
        self.assertEqual(config.read_bytes(), original)
        states = json.loads((self.ctx.env.state_dir / "template-consumers.json").read_text())
        self.assertTrue(states["kitty"])

    def test_generic_css_and_unknown_symlink_are_not_ownership(self):
        directory = self.ctx.home / ".config/gtk-3.0"
        directory.mkdir(parents=True)
        (directory / "gtk.css").write_text("@define-color accent_bg_color red;")
        (directory / "gtk-dark.css").symlink_to("gtk.css")
        hook = Path(__file__).resolve().parents[2] / "units/noctalia/hooks/remove-gtk-css"
        self.assertEqual(runpy.run_path(str(hook))["main"](), 0)
        self.assertTrue((directory / "gtk.css").is_file())
        self.assertTrue((directory / "gtk-dark.css").is_symlink())

    def test_optional_consumers_and_queued_render_follow_off_gate(self):
        env = self.ctx.env
        source = Path(__file__).resolve().parents[2] / "units/noctalia/noctalia-config.toml"
        config = env.config_dir / "noctalia/noctalia-config.toml"
        config.parent.mkdir()
        shutil.copyfile(source, config)
        for uid in ("noctalia", "theme", "kitty"):
            self.enable(uid)
        with patch("shutil.which", return_value=None):
            self.outputs.refresh_consumer_outputs()
        templates = tomllib.loads(config.read_text())["theme"]["templates"]["user"]
        self.assertIn("nyxuri_kitty", templates)
        self.assertNotIn("nyxuri_mango", templates)
        stage = env.state_dir / "template-staging/noctalia/nyxuri_kitty"
        stage.write_bytes(b"rendered")
        with patch("shutil.which", return_value=None):
            self.outputs.refresh_consumer_outputs({"kitty": False})
        self.assertTrue(self.outputs.commit_template("nyxuri_kitty"))
        self.assertFalse((env.config_dir / "kitty").exists())
        self.assertNotIn("nyxuri_kitty", tomllib.loads(config.read_text())["theme"]["templates"]["user"])

    def test_shell_gateway_check_preserves_personal_script(self):
        from nyxuri.desktop.shell_switcher import ensure_compositor_gateway_scripts
        directory = self.ctx.env.config_dir / "niri/scripts"
        directory.mkdir(parents=True)
        for name in ("session-shell.sh", "shell-action.sh"):
            script = directory / name
            script.write_bytes(b"#!/bin/sh\n# personal gateway\n")
            script.chmod(0o755)
        ensure_compositor_gateway_scripts()
        self.assertEqual((directory / "shell-action.sh").read_bytes(), b"#!/bin/sh\n# personal gateway\n")

    def test_snapshot_restores_output_and_original_metadata(self):
        target = self.ctx.home / ".config/gtk-3.0/gtk.css"
        self.outputs.write_output("noctalia", "theme", target, b"old")
        root = self.ctx.home / "snapshot"
        manifest = self.outputs.snapshot_state(root)
        self.outputs.write_output("noctalia", "theme", target, b"new")
        extra = self.ctx.home / ".config/mango/noctalia.conf"
        self.outputs.write_output("noctalia", "mango", extra, b"new output")
        self.outputs.restore_state(root, manifest)
        self.assertEqual(target.read_bytes(), b"old")
        self.assertFalse(extra.exists())
        self.outputs.withdraw_outputs()
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
