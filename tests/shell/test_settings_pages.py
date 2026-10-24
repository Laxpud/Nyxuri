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
    "ThemePage.qml": (
        "theme.section.settings-panel-style",
        "theme.section.matugen-color-scheme",
        "theme.section.transparency-and-blur",
        "theme.section.super-key-appearance",
        "theme.section.lock-screen",
        "theme.section.cursor-theme",
        "theme.section.icon-theme",
        "theme.section.fonts",
        "theme.section.matugen-template-generation",
    ),
    "WallpaperPage.qml": (
        "wallpaper.section.current-wallpaper",
        "wallpaper.section.transition",
        "wallpaper.section.parallax-effects",
        "wallpaper.section.overview-background",
    ),
    "GammaControlPage.qml": (
        "displays.gamma.section.color",
        "displays.gamma.section.schedule",
        "displays.gamma.section.current-status",
    ),
    "DisplayConfigurationPage.qml": (
        "displays.configuration.section.layout",
        "displays.configuration.section.output-settings",
        "displays.configuration.section.hot-corners",
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

    def test_wallpaper_quick_pick_fills_the_row(self):
        source = _read("AccountPage.qml")
        # Adaptive full-row tiling: 6 columns wide / 2 rows of 3 narrow —
        # six choices always divide exactly. The pre-Nexus 152px cap (tuned
        # for a ~450px card, broke apart inside the 800px column) is dead.
        self.assertIn("wallpaperColumns", source)
        self.assertIn(">= 640 ? 6 : 3", source)
        self.assertNotIn("wallpaperPreviewMaximumWidth", source,
                         "the old tile-width cap must not come back")
        self.assertIn("Layout.columnSpan", source, "the empty placeholder spans the row")
        self.assertIn("WallpaperService.currentWallpaper === wallpaperChoice.modelData", source,
                      "the current wallpaper carries a selection ring")

    def test_legacy_chrome_stays_out(self):
        source = _read("AccountPage.qml")
        for token in LEGACY_VOCABULARY:
            self.assertNotIn(token, source, f"legacy token re-entered AccountPage: {token}")


class TestThemePageRebuild(unittest.TestCase):
    """ThemePage: atoms for every standard row, semantic pickers stay custom."""

    def test_nexus_scaffold_with_self_rendered_title(self):
        source = _read("ThemePage.qml")
        self.assertIn("NexusPageBase {", source)
        self.assertIn('title: I18n.tr("Theme")', source)

    def test_window_contract_surface_survives(self):
        source = _read("ThemePage.qml")
        for token in (
            "property var parentModal: null",
            "property var pendingDeleteTemplate: null",
            "function requestTemplateDeletion(",
            "function closeChildWindows()",
            "property Item searchLeaf",
        ):
            self.assertIn(token, source, f"ThemePage lost window contract token: {token}")

    def test_search_anchor_ids_are_stable(self):
        source = _read("ThemePage.qml")
        for anchor_id in ANCHOR_IDS["ThemePage.qml"]:
            self.assertIn(f'\\"id\\":\\"{anchor_id}\\"'.replace("\\\"", '"'), source,
                          f"anchor missing or rewritten: {anchor_id}")

    def test_atom_groups_present(self):
        source = _read("ThemePage.qml")
        for atom in ("PreferenceHeader", "PreferenceToggle", "PreferenceSlider", "PreferenceSelect"):
            self.assertIn(atom, source, f"ThemePage must use the atom: {atom}")
        # Every select row registers the compositor input region.
        self.assertEqual(source.count("inputRegionService: PopupInputRegionService"), 6)

    def test_business_owners_unchanged(self):
        source = _read("ThemePage.qml")
        for owner in (
            "ThemeService.setThemeMode",
            "ThemeService.setMatugenScheme",
            "ThemeService.setCursorTheme",
            "ThemeService.setCursorSize",
            "ThemeService.setCursorHideWhenTyping",
            "ThemeService.setCursorHideAfterInactiveMs",
            "ThemeService.setIconTheme",
            "ThemeService.setMatugenTemplateEnabled",
            "PersonalizationConfig.setShellBackgroundOpacity",
            "PersonalizationConfig.setShellBlurEnabled",
            "PersonalizationConfig.setShellBlurXray",
            "PersonalizationConfig.setLockScreenStyle",
            "PersonalizationConfig.setFontFamily",
            "NiriConfigService.refresh()",
            "BlurService.available",
            "FontService.fontOptions",
            "TemplateService.remove",
        ):
            self.assertIn(owner, source, f"business owner dropped: {owner}")

    def test_semantic_pickers_survive_as_custom_shapes(self):
        source = _read("ThemePage.qml")
        for shape in (
            "component ThemePreviewCard:",
            "SettingsPanelStyleCard",
            "StyledButtonGroup",
            "CursorThemeSelect",
            "ShortcutKeycap",
            "MiniMaterialWaveLine",
        ):
            self.assertIn(shape, source, f"sanctioned custom shape dropped: {shape}")

    def test_inline_pre_m3_row_components_are_dead(self):
        source = _read("ThemePage.qml")
        for token in ("component Section:", "SearchSelectSettingRow", "ToggleSettingRow",
                      "SliderSettingRow"):
            self.assertNotIn(token, source, f"pre-M3 inline row component survived: {token}")

    def test_legacy_chrome_stays_out(self):
        source = _read("ThemePage.qml")
        for token in LEGACY_VOCABULARY:
            self.assertNotIn(token, source, f"legacy token re-entered ThemePage: {token}")


class TestWallpaperPageRebuild(unittest.TestCase):
    """WallpaperPage: preview/easing/button-group heroes stay, rows are atoms."""

    def test_nexus_scaffold_with_self_rendered_title(self):
        source = _read("WallpaperPage.qml")
        self.assertIn("NexusPageBase {", source)
        self.assertIn('title: I18n.tr("Wallpaper")', source)

    def test_window_contract_surface_survives(self):
        source = _read("WallpaperPage.qml")
        for token in (
            "property var parentModal: null",
            "function closeChildWindows()",
            "function chooseWallpaperFile()",
            "function chooseOverviewFile()",
            "property Item searchLeaf",
        ):
            self.assertIn(token, source, f"WallpaperPage lost window contract token: {token}")

    def test_search_anchor_ids_are_stable(self):
        source = _read("WallpaperPage.qml")
        for anchor_id in ANCHOR_IDS["WallpaperPage.qml"]:
            self.assertIn(f'\\"id\\":\\"{anchor_id}\\"'.replace("\\\"", '"'), source,
                          f"anchor missing or rewritten: {anchor_id}")

    def test_atom_groups_present(self):
        source = _read("WallpaperPage.qml")
        for atom in ("PreferenceHeader", "PreferenceToggle", "PreferenceSlider", "PreferenceSelect"):
            self.assertIn(atom, source, f"WallpaperPage must use the atom: {atom}")
        # Both output selectors register the compositor input region.
        self.assertEqual(source.count("inputRegionService: PopupInputRegionService"), 3)

    def test_business_owners_unchanged(self):
        source = _read("WallpaperPage.qml")
        for owner in (
            "WallpaperService.setWallpaperFromFile",
            "WallpaperService.setWallpaperFolder",
            "WallpaperService.setWallpaperFillModeForScreen",
            "WallpaperService.setWallpaperTransitionType",
            "WallpaperService.setTransitionDurationMs",
            "WallpaperService.setTransitionBezierCurve",
            "WallpaperService.setTransitionEasingMode",
            "WallpaperService.setOverviewFillModeForScreen",
            "WallpaperService.setOverviewWallpaper",
            "WallpaperService.refreshOverviewBackdropRule()",
            "PersonalizationConfig.setPerMonitorWallpaper",
            "PersonalizationConfig.setParallaxPreferredScale",
            "PersonalizationConfig.setParallaxTiledColumnSpan",
            "PersonalizationConfig.setOverviewTransitionType",
            "PersonalizationConfig.setOverviewBlurRadius",
            "PersonalizationConfig.setOverviewDim",
            "PersonalizationConfig.setOverviewSaturation",
            "PersonalizationConfig.setOverviewContrast",
        ):
            self.assertIn(owner, source, f"business owner dropped: {owner}")

    def test_visual_assets_survive_as_custom_shapes(self):
        source = _read("WallpaperPage.qml")
        for shape in (
            "component WallpaperPreview:",
            "component EasingActionGroup:",
            "BezierCurveEditor",
            "BezierCurveLayerEditor",
            "WallpaperFileBrowser",
            "WallpaperColorPicker",
            "NiriSetupPrompt",
        ):
            self.assertIn(shape, source, f"sanctioned custom shape dropped: {shape}")

    def test_inline_pre_m3_row_components_are_dead(self):
        source = _read("WallpaperPage.qml")
        for token in ("component Section:", "FlatSettingsSection", "SettingsRow", "MaterialSlider"):
            self.assertNotIn(token, source, f"pre-M3 inline row component survived: {token}")

    def test_legacy_chrome_stays_out(self):
        source = _read("WallpaperPage.qml")
        for token in LEGACY_VOCABULARY:
            self.assertNotIn(token, source, f"legacy token re-entered WallpaperPage: {token}")


class TestDisplaysPagesRebuild(unittest.TestCase):
    """Displays shell + both subpages: row-level atoms, machinery kept."""

    def test_shell_claims_title_and_keeps_routing(self):
        source = _read("DisplaysPage.qml")
        self.assertIn("readonly property bool rendersPageTitle: true", source,
                      "subpages render titles; the window shim must yield")
        for token in ("function openSearchPath(", "searchLeaf", "closeChildWindows",
                      "DisplayConfigService.clearCompletionNotice()",
                      'SpotlightCatalog.route("displays." + root.section)'):
            self.assertIn(token, source, f"DisplaysPage lost routing token: {token}")

    def test_subpages_are_nexus_scaffolded(self):
        for name, title_route in (("DisplayConfigurationPage.qml", "displays.configuration"),
                                  ("GammaControlPage.qml", "displays.gamma")):
            source = _read(name)
            self.assertIn("NexusPageBase {", source, name)
            self.assertIn(f'title: SpotlightCatalog.title("{title_route}")', source, name)
            self.assertIn("property Item searchLeaf", source, name)

    def test_search_anchor_ids_are_stable(self):
        for name in ("GammaControlPage.qml", "DisplayConfigurationPage.qml"):
            source = _read(name)
            for anchor_id in ANCHOR_IDS[name]:
                self.assertIn(f'\\"id\\":\\"{anchor_id}\\"'.replace("\\\"", '"'), source,
                              f"{name}: anchor missing or rewritten: {anchor_id}")

    def test_gamma_form_is_fully_atomized(self):
        source = _read("GammaControlPage.qml")
        for atom in ("PreferenceHeader", "PreferenceToggle", "PreferenceSlider", "PreferenceSelect",
                     "PreferenceInput", "PreferenceInfo", "PreferenceAction"):
            self.assertIn(atom, source, f"GammaControlPage must use the atom: {atom}")
        for owner in ("DisplayColor.setPreference", "DisplayColor.setDimming", "DisplayColor.locate()",
                      "DisplayColor.useWeatherLocation()"):
            self.assertIn(owner, source, f"business owner dropped: {owner}")
        for dead in ("SidebarFlickable", "SettingsSection", "SettingsRow", "GeneralSliderSetting",
                     "DisplayChoice", "OutlinedTextField", "StyledSwitch"):
            self.assertNotIn(dead, source, f"pre-M3 vocabulary survived in GammaControlPage: {dead}")
        for token in LEGACY_VOCABULARY:
            self.assertNotIn(token, source, f"legacy token re-entered GammaControlPage: {token}")

    def test_display_configuration_keeps_machinery_and_atomizes_rows(self):
        source = _read("DisplayConfigurationPage.qml")
        for atom in ("PreferenceToggle", "PreferenceSelect", "PreferenceInput", "PreferenceAction",
                     "PreferenceHeader"):
            self.assertIn(atom, source, f"DisplayConfigurationPage must use the atom: {atom}")
        # The transaction flow and custom editors survive.
        for kept in ("DisplayConfigService.apply()", "DisplayConfigService.reload()",
                     "DisplayConfigService.forget(", "DisplayLayoutCanvas", "DisplayAdvancedSettings",
                     "DisplayHotCornerSettings", "FloatingWindow", "CompositorBlurRegion"):
            self.assertIn(kept, source, f"machinery dropped: {kept}")
        # Mechanical rows left the old vocabulary (the kept-custom scale
        # dialog still hosts one OutlinedTextField of its own).
        for dead in ("DisplayChoice", "SettingsRow", "SettingsActionRow", "GridLayout"):
            self.assertNotIn(dead, source, f"pre-M3 row survived: {dead}")


if __name__ == "__main__":
    unittest.main()
