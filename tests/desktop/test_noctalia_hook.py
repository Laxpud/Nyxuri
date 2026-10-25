"""验证 GTK 渲染钩子的真实返回值与 IPC 顺序，避免复制配置被当成渲染成功。"""

import contextlib
import io
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


if __name__ == "__main__":
    unittest.main()
