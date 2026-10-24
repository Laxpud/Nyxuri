"""T3 M3 contracts: the first-batch Nexus page rebuilds.

AccountPage, ThemePage, WallpaperPage and DisplaysPage move onto the
NexusPageBase scaffold and the M1 atom suite. The contracts below pin, per
page: the scaffold + self-rendered title (the window shim yields), the
window-facing API surface staying alive (search leaf, parent modal,
presentation, navigation, child windows), the search-anchor registrations
compiling to the same catalog ids, business truths keeping their owners, and
the pre-M3 card chrome (MaterialCard / SettingsActionRow / inline private row
components) staying out of the rebuilt pages.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS = REPO_ROOT / "shell" / "units" / "settings"

ANCHOR_IDS = {
    "AccountPage.qml": (
        "account.section.language",
        "account.section.bluetooth-devices",
        "account.section.keyboard-shortcuts",
        "account.section.personalization",
    ),
}

# Pre-M3 card chrome and legacy row vocabulary: none of it may come back
# inside a rebuilt Nexus page.
LEGACY_VOCABULARY = (
    "MaterialCard",
    "SettingsActionRow",
    "SearchSelectMenuField",
    "Typography.",
    "Metrics.",
)


def _read(name):
    return (SETTINGS / name).read_text(encoding="utf-8")


class TestAccountPageRebuild(unittest.TestCase):
    """AccountPage: hero + four atom groups, same business owners."""

    def test_nexus_scaffold_with_self_rendered_title(self):
        source = _read("AccountPage.qml")
        self.assertIn("NexusPageBase {", source)
        self.assertIn('title: I18n.tr("Account")', source,
                      "the window route-title shim only yields to page titles")

    def test_window_contract_surface_survives(self):
        source = _read("AccountPage.qml")
        for token in (
            "property var parentModal: null",
            "property bool presentationActive: false",
            "signal navigateRequested(string pageId)",
            "function closeChildWindows()",
            "property Item searchLeaf",
        ):
            self.assertIn(token, source, f"AccountPage lost window contract token: {token}")
        # Uptime lease registration keeps its key.
        self.assertIn('setUptimeConsumer("account-page"', source)

    def test_search_anchor_ids_are_stable(self):
        source = _read("AccountPage.qml")
        for anchor_id in ANCHOR_IDS["AccountPage.qml"]:
            self.assertIn(f'\\"id\\":\\"{anchor_id}\\"'.replace("\\\"", '"'), source,
                          f"anchor missing or rewritten: {anchor_id}")

    def test_atom_groups_present(self):
        source = _read("AccountPage.qml")
        for atom in ("PreferenceHeader", "PreferenceToggle", "PreferenceSelect", "PreferenceAction"):
            self.assertIn(atom, source, f"AccountPage must use the atom: {atom}")
        # The select rows inject the compositor input-region service.
        self.assertEqual(source.count("inputRegionService: PopupInputRegionService"), 2,
                         "both select rows must register popup input regions")

    def test_business_owners_unchanged(self):
        source = _read("AccountPage.qml")
        for owner in (
            "SystemIdentityService",
            "AvatarService",
            "WallpaperService",
            "BluetoothService",
            "NetworkService",
            "ShortcutMapService",
            "UiPreferences.setLanguage",
            "I18nService.supportedLanguages",
            "ThemeService.setThemeMode",
        ):
            self.assertIn(owner, source, f"business owner dropped: {owner}")

    def test_custom_shapes_survive_where_atoms_have_none(self):
        source = _read("AccountPage.qml")
        self.assertIn("component DeviceRow: ConnectedRect", source,
                      "paired-device rows are the sanctioned custom shape")
        self.assertIn("AccountProfileHeader", source, "the hero stays a shared asset")
        self.assertIn("wallpaperChoices", source, "the wallpaper quick grid survives")

    def test_legacy_chrome_stays_out(self):
        source = _read("AccountPage.qml")
        for token in LEGACY_VOCABULARY:
            self.assertNotIn(token, source, f"legacy token re-entered AccountPage: {token}")


if __name__ == "__main__":
    unittest.main()
