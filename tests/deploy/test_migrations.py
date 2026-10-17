import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.utils import TempEnv
from nyxuri.core import get_compat_env


class TestMigrations(unittest.TestCase):
    def setUp(self):
        self.ctx = TempEnv()
        self.ctx.__enter__()

    def tearDown(self):
        self.ctx.__exit__()

    def test_runner_is_idempotent_and_records_level(self):
        from nyxuri import migrations

        with patch.object(migrations, "TOMBSTONES", (".cache/obsolete",)):
            old = self.ctx.home / ".cache/obsolete"
            old.parent.mkdir(parents=True, exist_ok=True)
            old.write_text("old", encoding="utf-8")
            self.assertTrue(migrations.run())
            self.assertFalse(old.exists())
            self.assertTrue(migrations.run())
        ledger = json.loads((self.ctx.env.state_dir / "state.json").read_text())
        self.assertEqual(ledger["migration_level"], migrations.MIGRATION_LEVEL)

    def test_tombstone_cannot_escape_home(self):
        from nyxuri import migrations

        outside = Path("/tmp/nyxuri-migration-test-outside")
        with patch.object(migrations, "TOMBSTONES", ("../nyxuri-migration-test-outside",)):
            self.assertFalse(migrations.run())
        self.assertFalse(outside.exists())

    def test_update_ledger_merges_nested_dicts(self):
        from nyxuri.kernel.ledger import read_ledger, update_ledger

        update_ledger(modules={"fcitx": True})
        update_ledger(modules={"fisher": True})
        ledger = read_ledger()
        self.assertEqual(ledger["modules"], {"fcitx": True, "fisher": True})


# --- merged from test_legacy_migration.py (KM3.5 测试镜像树) ---

"""Legacy storage migration must never lose data.

Regression guard: when a file existed in the legacy tree and the destination
already held the same name as a BROKEN symlink, _merge_directory_contents
skipped the copy but still reported success — so _safe_migrate_storage_dir
deleted the legacy tree and the user's file was gone with no error.
"""

import tempfile
import unittest
from pathlib import Path

from nyxuri.core import _merge_directory_contents, _safe_migrate_storage_dir


class TestLegacyStorageMigration(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _pair(self, name):
        legacy = self.tmp / f"{name}-legacy"
        target = self.tmp / f"{name}-target"
        legacy.mkdir()
        target.mkdir()
        return legacy, target

    def test_clean_migration_moves_and_removes_legacy(self):
        legacy, target = self._pair("clean")
        (legacy / "x.txt").write_text("X")
        _safe_migrate_storage_dir(legacy, target)
        self.assertEqual((target / "x.txt").read_text(), "X")
        self.assertFalse(legacy.exists())

    def test_existing_target_file_wins_and_legacy_is_removed(self):
        legacy, target = self._pair("existing")
        (legacy / "y.txt").write_text("Y")
        (target / "y.txt").write_text("EXISTING")
        _safe_migrate_storage_dir(legacy, target)
        self.assertEqual((target / "y.txt").read_text(), "EXISTING")
        self.assertFalse(legacy.exists())

    def test_valid_symlink_target_is_treated_as_present(self):
        legacy, target = self._pair("validlink")
        (legacy / "z.txt").write_text("Z")
        (target / "real.txt").write_text("REAL")
        (target / "z.txt").symlink_to(target / "real.txt")
        _safe_migrate_storage_dir(legacy, target)
        self.assertFalse(legacy.exists())
        self.assertEqual((target / "z.txt").read_text(), "REAL")

    def test_broken_symlink_target_keeps_legacy_tree(self):
        legacy, target = self._pair("brokenlink")
        (legacy / "a.txt").write_text("IMPORTANT USER DATA")
        (legacy / "b.txt").write_text("also important")
        (target / "a.txt").symlink_to(self.tmp / "does-not-exist")

        _safe_migrate_storage_dir(legacy, target)

        self.assertTrue(legacy.exists(), "legacy tree must survive an incomplete merge")
        self.assertEqual((legacy / "a.txt").read_text(), "IMPORTANT USER DATA")
        self.assertEqual((legacy / "b.txt").read_text(), "also important")

    def test_merge_reports_failure_for_broken_symlink_target(self):
        legacy, target = self._pair("report")
        (legacy / "a.txt").write_text("DATA")
        (target / "a.txt").symlink_to(self.tmp / "nope")
        self.assertFalse(_merge_directory_contents(legacy, target))

    def test_nested_merge_copies_missing_files(self):
        legacy, target = self._pair("nested")
        (legacy / "sub").mkdir()
        (legacy / "sub" / "deep.txt").write_text("DEEP")
        (target / "sub").mkdir()
        (target / "sub" / "old.txt").write_text("OLD")
        _safe_migrate_storage_dir(legacy, target)
        self.assertEqual((target / "sub" / "deep.txt").read_text(), "DEEP")
        self.assertEqual((target / "sub" / "old.txt").read_text(), "OLD")
        self.assertFalse(legacy.exists())

    def test_symlinked_legacy_dir_is_removed_not_followed(self):
        real = self.tmp / "real"
        real.mkdir()
        (real / "keep.txt").write_text("KEEP")
        link = self.tmp / "legacy-link"
        link.symlink_to(real)

        _safe_migrate_storage_dir(link, self.tmp / "target-link")

        self.assertFalse(link.exists())
        self.assertTrue((real / "keep.txt").exists())


# --- merged from test_migration_rebrand.py (KM3.5 测试镜像树) ---

"""Contract tests for NyxNiri -> Nyxuri rebranding and storage migration."""

import os
from pathlib import Path
import unittest

from tests.utils import TempEnv
from nyxuri.core import get_compat_env

from nyxuri.core import (
    ensure_nyxuri_symlink,
    is_nyxuri_cli_symlink,
    migrate_legacy_storage,
)


class TestRebrandStorageMigration(unittest.TestCase):
    """Legacy NyxNiri directories migrate cleanly into nyxuri with zero residue."""

    def test_legacy_config_and_state_migration(self):
        with TempEnv() as ctx:
            env = ctx.env
            legacy_config = env.home / ".config" / "NyxNiri"
            legacy_config.mkdir(parents=True, exist_ok=True)
            (legacy_config / "marker.txt").write_text("config_payload", encoding="utf-8")

            legacy_state = env.home / ".local" / "state" / "NyxNiri"
            legacy_state.mkdir(parents=True, exist_ok=True)
            (legacy_state / "state.log").write_text("log_payload", encoding="utf-8")

            legacy_cache = env.home / ".cache" / "nyxniri"
            legacy_cache.mkdir(parents=True, exist_ok=True)
            (legacy_cache / "cached.dat").write_text("cache_payload", encoding="utf-8")

            migrate_legacy_storage(env)

            # Old directories must not exist
            self.assertFalse(legacy_config.exists(), "Legacy config directory must be removed")
            self.assertFalse(legacy_state.exists(), "Legacy state directory must be removed")
            self.assertFalse(legacy_cache.exists(), "Legacy cache directory must be removed")

            # New directories must contain the migrated payloads
            self.assertTrue(env.nyx_dir.is_dir())
            self.assertEqual((env.nyx_dir / "marker.txt").read_text(encoding="utf-8"), "config_payload")
            self.assertEqual((env.state_dir / "state.log").read_text(encoding="utf-8"), "log_payload")
            self.assertEqual((env.cache_dir / "cached.dat").read_text(encoding="utf-8"), "cache_payload")

    def test_recursive_directory_merge(self):
        """When target directory already exists, nested directories must merge recursively without data loss."""
        with TempEnv() as ctx:
            env = ctx.env
            # Target already has presets/niri.active and presets/custom_preset/item1
            (env.nyx_dir / "presets" / "custom_preset").mkdir(parents=True, exist_ok=True)
            (env.nyx_dir / "presets" / "niri.active").write_text("active_target", encoding="utf-8")
            (env.nyx_dir / "presets" / "custom_preset" / "item1.kdl").write_text("item1_target", encoding="utf-8")

            # Legacy has presets/custom_preset/item1 (collision) and presets/custom_preset/item2 (new)
            legacy_config = env.home / ".config" / "NyxNiri"
            (legacy_config / "presets" / "custom_preset").mkdir(parents=True, exist_ok=True)
            (legacy_config / "presets" / "custom_preset" / "item1.kdl").write_text("item1_legacy", encoding="utf-8")
            (legacy_config / "presets" / "custom_preset" / "item2.kdl").write_text("item2_legacy", encoding="utf-8")
            (legacy_config / "presets" / "legacy_preset").mkdir(parents=True, exist_ok=True)
            (legacy_config / "presets" / "legacy_preset" / "item3.kdl").write_text("item3_legacy", encoding="utf-8")

            migrate_legacy_storage(env)

            self.assertFalse(legacy_config.exists())
            # Existing target files preserved
            self.assertEqual((env.nyx_dir / "presets" / "niri.active").read_text(encoding="utf-8"), "active_target")
            self.assertEqual((env.nyx_dir / "presets" / "custom_preset" / "item1.kdl").read_text(encoding="utf-8"), "item1_target")
            # Legacy files merged in
            self.assertEqual((env.nyx_dir / "presets" / "custom_preset" / "item2.kdl").read_text(encoding="utf-8"), "item2_legacy")
            self.assertEqual((env.nyx_dir / "presets" / "legacy_preset" / "item3.kdl").read_text(encoding="utf-8"), "item3_legacy")

    def test_legacy_cli_link_purged_on_ensure(self):
        with TempEnv() as ctx:
            env = ctx.env
            bin_dir = env.home / ".local/bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            legacy_link = bin_dir / "nyxniri"
            installer = env.repo_dir / "install.sh"
            installer.touch()
            legacy_link.symlink_to(installer)

            self.assertTrue(is_nyxuri_cli_symlink(legacy_link))
            ensure_nyxuri_symlink()

            new_link = bin_dir / "nyxuri"
            self.assertTrue(new_link.is_symlink())
            self.assertEqual(new_link.resolve(), installer.resolve())
            self.assertFalse(legacy_link.exists(), "Legacy CLI symlink must be purged")


class TestCompatEnv(unittest.TestCase):
    """Backward-compatible environment variable resolution."""

    def test_nyxuri_takes_precedence_over_nyxniri(self):
        env_vars = {
            "NYXURI_CUSTOM_SHELL": "/bin/zsh",
            "NYXNIRI_CUSTOM_SHELL": "/bin/bash",
        }
        with unittest.mock.patch.dict(os.environ, env_vars, clear=False):
            self.assertEqual(get_compat_env("CUSTOM_SHELL"), "/bin/zsh")

    def test_fallback_to_legacy_nyxniri(self):
        env_vars = {
            "NYXNIRI_CUSTOM_SHELL": "/bin/fish",
        }
        with unittest.mock.patch.dict(os.environ, env_vars, clear=False):
            if "NYXURI_CUSTOM_SHELL" in os.environ:
                del os.environ["NYXURI_CUSTOM_SHELL"]
            self.assertEqual(get_compat_env("CUSTOM_SHELL"), "/bin/fish")
