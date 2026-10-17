"""Tests verifying AI specification integrity and preventing documentation drift.

Gate set for llms-wiki/docs-charter.md:
  - AGENTS.md stays compact and routes to the wiki
  - llms-wiki/llms.txt links resolve and no live page is orphaned
  - Live-area relative links resolve (upstream/ + archive/ are frozen and exempt)
  - ROADMAP status vocabulary stays canonical
  - CLI commands stay documented in operation-map.md
"""

import re
import unittest
from pathlib import Path


class TestAISpecs(unittest.TestCase):
    """Ensure AI directives, architecture wiki, and index links stay unbroken."""

    def setUp(self):
        self.root_dir = Path(__file__).resolve().parent.parent
        self.wiki_dir = self.root_dir / "llms-wiki"
        self.llms_txt = self.wiki_dir / "llms.txt"
        self.agents_md = self.root_dir / "AGENTS.md"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _live_md_files(self):
        """Live-area markdown: both AGENTS, both ROADMAPs, docs-charter, and
        every llms-wiki page outside upstream/ and archive/."""
        files = [
            self.root_dir / "AGENTS.md",
            self.root_dir / "ROADMAP.md",
            self.root_dir / "shell" / "AGENTS.md",
            self.root_dir / "shell" / "ROADMAP.md",
        ]
        for page in self.wiki_dir.rglob("*.md"):
            rel = page.relative_to(self.wiki_dir).as_posix()
            if rel.startswith(("upstream/", "archive/")):
                continue
            files.append(page)
        return files

    @staticmethod
    def _relative_links(text):
        for match in re.findall(r"\]\(([^)]+)\)", text):
            link = match.split("#", 1)[0].strip()
            if link and not link.startswith(("http://", "https://", "mailto:")):
                yield link

    # ------------------------------------------------------------------
    # AGENTS.md contract
    # ------------------------------------------------------------------

    def test_agents_md_exists_and_compact(self):
        """AGENTS.md must exist at root, be concise (~100 lines), and reference routing."""
        self.assertTrue(self.agents_md.is_file(), "AGENTS.md must exist at root")
        content = self.agents_md.read_text(encoding="utf-8")
        lines = content.strip().splitlines()
        self.assertLess(len(lines), 150, f"AGENTS.md should stay concise, got {len(lines)} lines")
        self.assertIn("llms-wiki/llms.txt", content)
        self.assertIn("必读 Wiki 契约", content)

    def test_agents_md_links_resolve(self):
        """Every relative link in both AGENTS.md files must resolve."""
        for agents in (self.agents_md, self.root_dir / "shell" / "AGENTS.md"):
            for link in self._relative_links(agents.read_text(encoding="utf-8")):
                target = (agents.parent / link).resolve()
                self.assertTrue(target.exists(), f"Broken link in {agents.name}: {link} -> {target}")

    # ------------------------------------------------------------------
    # llms.txt index
    # ------------------------------------------------------------------

    def test_llms_txt_links_resolve(self):
        """Every link referenced in llms-wiki/llms.txt must resolve to an existing non-empty file."""
        self.assertTrue(self.llms_txt.is_file(), "llms-wiki/llms.txt must exist")
        content = self.llms_txt.read_text(encoding="utf-8")
        links = re.findall(r"\[.*?\]\((.*?)\)", content)
        self.assertGreater(len(links), 15, "llms.txt should index core architecture topics")

        for link in links:
            target = (self.wiki_dir / link).resolve()
            self.assertTrue(target.exists(), f"Broken link in llms.txt: {link} -> {target}")
            self.assertGreater(target.stat().st_size, 0, f"Referenced file is empty: {target}")

    def test_llms_txt_covers_all_live_pages(self):
        """Bidirectional index closure: every live wiki page is indexed in llms.txt."""
        content = self.llms_txt.read_text(encoding="utf-8")
        for page in self._live_md_files():
            if page == self.llms_txt or page.parent != self.wiki_dir:
                continue
            name = page.relative_to(self.wiki_dir).as_posix()
            if name == "docs-charter.md":
                self.assertIn("(docs-charter.md)", content, f"Live page not indexed: {name}")
            else:
                self.assertIn(f"({name})", content, f"Live page not indexed: {name}")

    def test_new_domain_topics_indexed(self):
        """Ensure domain topics and guidelines are strictly indexed in llms.txt."""
        content = self.llms_txt.read_text(encoding="utf-8")
        for topic in (
            "i18n.md",
            "assets-deploy.md",
            "backup-snapshot.md",
            "packaging.md",
            "writing-voice.md",
            "changelog-spec.md",
            "tui-charter.md",
            "vision.md",
            "agent-rules-provenance.md",
            "docs-charter.md",
        ):
            self.assertIn(topic, content, f"Domain topic {topic} must be indexed in llms.txt")

    # ------------------------------------------------------------------
    # Live-area link hygiene (docs-charter: L2 pages must not dangle)
    # ------------------------------------------------------------------

    def test_live_docs_links_resolve(self):
        """Every relative link in the live area must resolve; upstream/ and archive/ are frozen-exempt."""
        checked = 0
        for page in self._live_md_files():
            for link in self._relative_links(page.read_text(encoding="utf-8")):
                target = (page.parent / link).resolve()
                self.assertTrue(
                    target.exists(),
                    f"Broken live-area link in {page.relative_to(self.root_dir)}: {link} -> {target}",
                )
                checked += 1
        self.assertGreater(checked, 30, "Live-area link scan should cover the real doc graph")

    def test_live_docs_do_not_reference_dissolved_paths(self):
        """Retired locations must not creep back into live docs."""
        banned = ("shell/wiki/", "wiki/tree-inventory", "wiki/upstream-docs", "noctalia-llm-docs")
        for page in self._live_md_files():
            text = page.read_text(encoding="utf-8")
            for fragment in banned:
                self.assertNotIn(
                    fragment,
                    text,
                    f"{page.relative_to(self.root_dir)} still references retired path: {fragment}",
                )

    # ------------------------------------------------------------------
    # ROADMAP status vocabulary (docs-charter: canonical status words)
    # ------------------------------------------------------------------

    def test_shell_roadmap_status_vocabulary(self):
        """shell/ROADMAP.md ledger rows may only use the five canonical statuses."""
        roadmap = (self.root_dir / "shell" / "ROADMAP.md").read_text(encoding="utf-8")
        allowed = {"待开始", "进行中", "阻断", "待验收", "已完成"}
        for match in re.findall(r"^\| (R[^|*]+) \| ([^|]+) \| ([^|]+) \|$", roadmap, re.MULTILINE):
            stage, _, status = (part.strip() for part in match)
            self.assertIn(status, allowed, f"Non-canonical status for {stage}: {status}")

    # ------------------------------------------------------------------
    # Unit-model death registry (unit-model.md §7, two-step enforcement)
    # ------------------------------------------------------------------

    def test_death_registry_open_rows_registered(self):
        """KM0 registration step: every not-yet-enforced death-row object must
        be registered in unit-model.md §7 with name and stage on the same row.

        Upgrade path (per ROADMAP): when a stage closes, its rows upgrade to
        physical-deletion assertions and retire from this registration list —
        KM1's three rows were enforced (see test_km1_death_row_enforced);
        KM5: cli hardcoded commands gone, installer demoted to bootstrap.
        """
        content = (self.wiki_dir / "unit-model.md").read_text(encoding="utf-8")
        rows = [line for line in content.splitlines() if line.startswith("|")]
        for name, stage in (
            ("nyxuri/cli.py", "KM5"),
            ("install.sh", "KM5"),
        ):
            self.assertTrue(
                any(name in row and stage in row for row in rows),
                f"death-row object '{name}' must be registered with stage {stage} in unit-model.md §7",
            )

    def test_km3_module_death_row_enforced(self):
        """KM3 enforcement step: nyxuri/modules/ is physically deleted — the
        dedicated business modules live on as configs/<unit>/hooks/ scripts,
        the engine holds zero references, and §7 marks the row enforced.
        """
        # 1. §7 row marked enforced.
        content = (self.wiki_dir / "unit-model.md").read_text(encoding="utf-8")
        rows = [line for line in content.splitlines() if line.startswith("|")]
        self.assertTrue(
            any("nyxuri/modules/" in row and "KM3（已执法" in row for row in rows),
            "death-row object 'nyxuri/modules/' must be marked KM3（已执法） in unit-model.md §7",
        )

        # 2. Physical absence of the package.
        self.assertFalse((self.root_dir / "nyxuri" / "modules").exists())

        # 3. Zero engine references to the retired package.
        for py in (self.root_dir / "nyxuri").rglob("*.py"):
            self.assertNotIn(
                "nyxuri.modules",
                py.read_text(encoding="utf-8"),
                f"{py.relative_to(self.root_dir)} still references the retired nyxuri.modules package",
            )

        # 4. The retired wiki page is gone and not indexed.
        self.assertFalse((self.wiki_dir / "modules.md").exists())
        llms_txt = (self.wiki_dir / "llms.txt").read_text(encoding="utf-8")
        self.assertNotIn("modules.md", llms_txt)

        # 5. The unit-owned hook scripts took over.
        hooks = self.root_dir / "configs"
        for unit, name in (
            ("fcitx5-rime", "activate"), ("fcitx5-rime", "deactivate"),
            ("fish", "install-fisher"), ("fish", "remove-fisher"),
            ("greeter", "activate"), ("greeter", "deactivate"),
            ("noctalia", "render-gtk"), ("noctalia", "remove-gtk-css"),
        ):
            self.assertTrue((hooks / unit / "hooks" / name).is_file(), f"{unit}/hooks/{name}")

    def test_km1_death_row_enforced(self):
        """KM1 enforcement step: the three sidecar mechanisms are physically
        deleted — their registration rows are retired, §7 marks them enforced,
        the blueprint carries no trace, and the engine holds zero references.
        """
        # 1. §7 rows marked enforced.
        content = (self.wiki_dir / "unit-model.md").read_text(encoding="utf-8")
        rows = [line for line in content.splitlines() if line.startswith("|")]
        for name in (".optional-apps.toml", "starship.toml.module.toml", "*.module.toml"):
            self.assertTrue(
                any(name in row and "KM1（已执法" in row for row in rows),
                f"death-row object '{name}' must be marked KM1（已执法） in unit-model.md §7",
            )

        # 2. Physical absence in the blueprint.
        configs = self.root_dir / "configs"
        self.assertFalse((configs / ".optional-apps.toml").exists())
        self.assertFalse((configs / "starship.toml").exists())
        self.assertEqual(list(configs.glob("**/*.module.toml")), [])
        # The single-file degenerate was upgraded to a proper unit directory.
        self.assertTrue((configs / "starship" / "starship.toml").is_file())
        self.assertTrue((configs / "starship" / "manifest.toml").is_file())

        # 3. Engine source holds zero references to the dead names.
        for py in sorted((self.root_dir / "nyxuri").rglob("*.py")):
            text = py.read_text(encoding="utf-8")
            for dead in (".module.toml", ".optional-apps.toml"):
                self.assertNotIn(dead, text, f"{py.relative_to(self.root_dir)} still references {dead}")

    # ------------------------------------------------------------------
    # CLI command mapping
    # ------------------------------------------------------------------

    def test_cli_commands_documented_in_operation_map(self):
        """Ensure all CLI commands in cli.py COMMANDS are documented in operation-map.md."""
        from nyxuri.cli import COMMANDS

        op_map = (self.wiki_dir / "operation-map.md").read_text(encoding="utf-8")
        for cmd in COMMANDS:
            if cmd in ("-h", "--help"):
                continue
            self.assertIn(
                f"`{cmd}",
                op_map,
                f"CLI command '{cmd}' is implemented in cli.py but missing from operation-map.md",
            )


if __name__ == "__main__":
    unittest.main()
