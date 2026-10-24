"""T3 M1 contracts: the Caelestia-style preference atom suite.

The atoms land in shell/units/settings/controls/ as a pure-QML presentation
library: every row extends ConnectedRect (the connected-card group form),
theme truth comes exclusively from the Nyxuri singletons (Appearance,
Typography, Metrics, Fonts) and every user-visible string goes through I18n.
These tests pin the per-atom API surface so M3 page rebuilds cannot silently
drift it, and keep the pool free of upstream and side-effect imports.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTROLS = REPO_ROOT / "shell" / "units" / "settings" / "controls"

ATOMS = (
    "ConnectedRect.qml",
    "PreferenceHeader.qml",
    "PreferenceToggle.qml",
    "PreferenceSlider.qml",
    "PreferenceInput.qml",
    "PreferenceSelect.qml",
    "PreferenceStepper.qml",
    "PreferenceAction.qml",
    "PreferenceInfo.qml",
    "NexusSearchBar.qml",
    "NexusPageBase.qml",
)


def _source(name: str) -> str:
    return (CONTROLS / name).read_text(encoding="utf-8")


class TestSuiteShape(unittest.TestCase):
    """The pool exists, is complete, and holds nothing else."""

    def test_exactly_the_eleven_atoms_ship(self):
        self.assertTrue(CONTROLS.is_dir(), "controls/ directory missing")
        shipped = sorted(p.name for p in CONTROLS.glob("*.qml"))
        self.assertEqual(shipped, sorted(ATOMS), f"unexpected pool contents: {shipped}")

    def test_no_upstream_or_sideeffect_imports(self):
        forbidden = (
            "import Caelestia",
            "import qs.services",
            "import qs.modules",
            "import Quickshell",
            "import qs.app",
        )
        for name in ATOMS:
            source = _source(name)
            for token in forbidden:
                self.assertNotIn(token, source, f"{name} imports {token}")

    def test_theme_truth_is_the_nyxuri_singletons(self):
        for name in ATOMS:
            source = _source(name)
            self.assertIn("qs.shared.theme", source, f"{name} does not bridge theme tokens")
            self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b", source),
                              f"{name} hardcodes a hex color")


class TestConnectedForm(unittest.TestCase):
    """first/last drive the connected-card rounding; groups share the container color."""

    def test_radius_and_color_contract(self):
        source = _source("ConnectedRect.qml")
        self.assertIn("property bool first", source)
        self.assertIn("property bool last", source)
        self.assertIn("color: Appearance.m3colors.m3surfaceContainer", source)
        self.assertIn("first ? Appearance.rounding.extraLarge : Appearance.rounding.extraSmall", source)
        self.assertIn("last ? Appearance.rounding.extraLarge : Appearance.rounding.extraSmall", source)

    def test_row_atoms_sit_on_connected_rect(self):
        for name in ("PreferenceToggle.qml", "PreferenceSlider.qml", "PreferenceInput.qml",
                     "PreferenceSelect.qml", "PreferenceStepper.qml", "PreferenceAction.qml",
                     "PreferenceInfo.qml"):
            source = _source(name)
            self.assertRegex(source, re.compile(r"^ConnectedRect \{", re.MULTILINE),
                             f"{name} must root in ConnectedRect")

    def test_section_header_is_a_plain_label(self):
        source = _source("PreferenceHeader.qml")
        self.assertIn("property bool first", source)
        self.assertIn("Appearance.m3colors.m3onSurfaceVariant", source)
        self.assertIn("Typography.labelMedium", source)


class TestRowAtoms(unittest.TestCase):
    """Per-atom API surface pinned for the M3 page rebuilds."""

    def test_toggle_row(self):
        source = _source("PreferenceToggle.qml")
        self.assertIn("property alias checked: toggleItem.checked", source)
        self.assertRegex(source, r"signal toggled\b")
        # Whole-row activation: a row-level press area plus the pill switch.
        self.assertIn("onClicked: root.toggle()", source)
        self.assertIn("StyledSwitch {", source)
        self.assertIn("onToggled: root.toggled()", source)
        self.assertIn("StateLayer {", source)

    def test_slider_row(self):
        source = _source("PreferenceSlider.qml")
        self.assertIn("signal moved(real value)", source)
        self.assertIn("property real wheelStep:", source)
        self.assertIn("function onWheel(event: WheelEvent): void", source)
        # Slim Nexus slider: unstyled template Slider, visuals in contentItem.
        self.assertIn("import QtQuick.Templates", source)
        self.assertIn("property real pos: visualPosition", source)
        self.assertIn("when: dragArea.pressed", source)

    def test_input_row(self):
        source = _source("PreferenceInput.qml")
        self.assertIn("signal valueEdited(string value)", source)
        self.assertIn("signal editingFinished(string value)", source)
        self.assertIn("property var validate", source)
        self.assertIn("readonly property bool valid:", source)
        # Edits still pending when the page closes are flushed, not dropped.
        self.assertIn("Component.onDestruction:", source)
        self.assertIn("editingFinished(input.text)", source)
        # Breathing focus border + clear affordance.
        self.assertRegex(source, r"Behavior on border\.color")
        self.assertRegex(source, r"input\.activeFocus\s*\?\s*Appearance\.m3colors\.m3primary")
        self.assertIn('iconName: "close"', source)

    def test_select_row(self):
        source = _source("PreferenceSelect.qml")
        self.assertIn("property alias model: splitButton.model", source)
        self.assertIn("property alias currentValue: splitButton.currentValue", source)
        self.assertIn("signal selected(string value)", source)
        self.assertIn("SplitMenuButton {", source)
        # Compositor input regions are injected by the page, not read here.
        self.assertIn("property var inputRegionService: null", source)

    def test_stepper_row(self):
        source = _source("PreferenceStepper.qml")
        self.assertIn("signal moved(int value)", source)
        self.assertIn("MaterialStepper {", source)
        self.assertIn("onValueModified: value => root.moved(value)", source)

    def test_action_row(self):
        source = _source("PreferenceAction.qml")
        self.assertIn('property string trailingIcon: "chevron_right"', source)
        self.assertRegex(source, r"signal clicked\b")
        self.assertIn("animateChange: true", source)

    def test_info_row_is_readonly(self):
        source = _source("PreferenceInfo.qml")
        self.assertIn("property alias value: valueLabel.text", source)
        for token in ("MouseArea", "StateLayer", "signal clicked"):
            self.assertNotIn(token, source, f"PreferenceInfo must stay read-only: found {token}")


class TestWindowChrome(unittest.TestCase):
    """Search bar and page scaffold."""

    def test_search_bar_is_a_pill_textfield(self):
        source = _source("NexusSearchBar.qml")
        self.assertRegex(source, re.compile(r"^TextField \{", re.MULTILINE))
        self.assertIn("radius: Appearance.rounding.full", source)
        self.assertIn('text: "search"', source)
        self.assertIn("enabled: root.text.length > 0", source)
        self.assertIn("Behavior on border.color", source)

    def test_page_base_keeps_navigation_with_the_host(self):
        source = _source("NexusPageBase.qml")
        self.assertIn("required property string title", source)
        self.assertIn("property bool isSubPage: false", source)
        self.assertRegex(source, r"signal backRequested\b")
        self.assertNotIn("NexusState", source, "navigation state must not leak into the scaffold")
        self.assertIn("default property Item contentChild", source)
        self.assertIn("readonly property int cappedWidth: Math.min(maxContentWidth, width)", source)
        self.assertIn("contentItem.children: root.contentChild ? [root.contentChild] : []", source)


class TestWarmupAndI18n(unittest.TestCase):
    """KM4.6 rule + translation coverage for the atoms' own strings."""

    def test_controls_pool_is_in_the_slot_host_warmup(self):
        source = (REPO_ROOT / "shell" / "app" / "SlotHost.qml").read_text(encoding="utf-8")
        self.assertIn("import qs.units.settings.controls", source,
                      "new synthesized qs.* pool must warm up in SlotHost")

    def test_atom_strings_are_translated(self):
        zh = (REPO_ROOT / "shell" / "app" / "i18n" / "zh_CN.toml").read_text(encoding="utf-8")
        for key in ("Go back", "Clear"):
            self.assertIn(f'"{key}"', zh)


if __name__ == "__main__":
    unittest.main()
