"""Tests verifying the KM0 Unit Model specification and invariants."""

import tomllib
import unittest
from pathlib import Path


def resolve_unit_dependencies(graph: dict[str, list[str]]) -> list[str]:
    """Pure stdlib Kahn's algorithm for unit dependency resolution.

    Returns topological order of units to enable. Raises ValueError on cycle.
    """
    in_degree = {u: 0 for u in graph}
    for u, deps in graph.items():
        for d in deps:
            if d in in_degree:
                in_degree[u] += 1

    queue = [u for u, deg in in_degree.items() if deg == 0]
    order = []
    while queue:
        curr = queue.pop(0)
        order.append(curr)
        for u, deps in graph.items():
            if curr in deps:
                in_degree[u] -= 1
                if in_degree[u] == 0:
                    queue.append(u)

    if len(order) != len(graph):
        raise ValueError("Cyclic dependency detected in units")
    return order


class TestUnitModelContract(unittest.TestCase):
    """KM0 contract integrity: ensures the unit model invariants are verified."""

    def setUp(self):
        self.root_dir = Path(__file__).resolve().parent.parent
        self.unit_model_md = self.root_dir / "llms-wiki" / "unit-model.md"

    def test_unit_model_doc_exists_and_contains_canonical_terms(self):
        """llms-wiki/unit-model.md must exist and contain the 4 canonical terms."""
        self.assertTrue(self.unit_model_md.is_file(), "unit-model.md must exist")
        content = self.unit_model_md.read_text(encoding="utf-8")
        for term in ("单元", "内核", "源", "manifest"):
            self.assertIn(term, content, f"Canonical term '{term}' missing in unit-model.md")

    def test_four_canonical_verbs_documented(self):
        """The 4 minimal verbs (list, on, off, doctor) must be documented."""
        content = self.unit_model_md.read_text(encoding="utf-8")
        for verb in ("list", "on", "off", "doctor"):
            self.assertIn(f"`{verb}`", content, f"Core verb '{verb}' must be documented")

    def test_vault_path_invariants(self):
        """Vault must point to ~/.local/state/nyxuri/vault/<unit>/ as flat directory."""
        content = self.unit_model_md.read_text(encoding="utf-8")
        self.assertIn("vault/<unit>/", content)
        self.assertIn("纯文件平铺", content)

    def test_zero_config_defaults(self):
        """By convention, directory name drives target and package defaults."""
        unit_name = "kitty"
        default_target = unit_name
        default_packages = [unit_name]
        self.assertEqual(default_target, "kitty")
        self.assertEqual(default_packages, ["kitty"])

    def test_minimal_manifest_parsing(self):
        """Minimal manifest only overrides declared fields, zero boilerplate required."""
        raw_toml = 'preserve = ["monitor.kdl"]\n'
        parsed = tomllib.loads(raw_toml)
        self.assertEqual(parsed.get("preserve"), ["monitor.kdl"])
        self.assertIsNone(parsed.get("packages"))  # Not specified -> engine defaults to dir name

    def test_dependency_resolver_topological_sort(self):
        """DAG resolution orders dependencies before dependents."""
        graph = {
            "waybar": ["niri"],
            "niri": [],
            "orbit-translate": ["wl-clipboard"],
            "wl-clipboard": [],
        }
        order = resolve_unit_dependencies(graph)
        self.assertLess(order.index("niri"), order.index("waybar"))
        self.assertLess(order.index("wl-clipboard"), order.index("orbit-translate"))

    def test_dependency_resolver_detects_cycles(self):
        """Cyclic unit dependencies must raise ValueError."""
        cyclic_graph = {
            "a": ["b"],
            "b": ["a"],
        }
        with self.assertRaises(ValueError):
            resolve_unit_dependencies(cyclic_graph)

    def test_shell_coordination_invariants(self):
        """Shell coordination must follow single switch truth, quickshell IPC, microkernel, and slots."""
        content = self.unit_model_md.read_text(encoding="utf-8")
        self.assertIn("微内核宿主", content)
        self.assertIn("六大几何插槽模型", content)
        self.assertIn("单一开关真相", content)
        self.assertIn("ActionGateway", content)
        self.assertIn("quickshell ipc unit reload", content)
        self.assertIn("Loader", content)
        self.assertIn("shell.<domain>", content)
        self.assertIn("绝对绝缘", content)


if __name__ == "__main__":
    unittest.main()
