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
    "LanguageAndRegionPage.qml": (
        "language-region.section.language",
        "language-region.section.region-weather-location",
        "language-region.section.units",
        "language-region.section.time-date",
    ),
    "DefaultAppsPage.qml": (
        "default-apps.section.internet",
        "default-apps.section.utilities",
        "default-apps.section.documents",
        "default-apps.section.multimedia",
    ),
    "SpotlightPage.qml": (
        "spotlight.section.applications",
        "spotlight.section.web-search",
        "spotlight.section.clipboard",
    ),
    "ShellPage.qml": (
        "shell.section.modules",
        "shell.section.log",
        "shell.section.sampling",
        "shell.section.diagnostics",
    ),
    "GeneralBarPage.qml": (
        "bar.section.position",
        "bar.section.components",
    ),
    "DockPage.qml": (
        "dock.section.appearance",
        "dock.section.behavior",
        "dock.section.previews",
    ),
    "GeneralSidebarPage.qml": (
        "sidebar.section.sidebars",
        "sidebar.section.desktop-card-layout",
        "sidebar.section.clock-style",
        "sidebar.section.system-cards",
    ),
    "KeystonePage.qml": (
        "keystone.section.keystone-style",
        "keystone.section.mouse-actions",
        "keystone.section.media-controls",
        "keystone.section.keyboard-indicators",
        "keystone.section.keyhole",
        "keystone.section.horizontal-clock",
        "keystone.section.recording",
    ),
    "HorizontalClockPage.qml": (
        "keystone.horizontal-clock.section.horizontal-clock-style",
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
            self.assertIn(f'"id":"{anchor_id}"', source,
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
            self.assertIn(f'"id":"{anchor_id}"', source,
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
            self.assertIn(f'"id":"{anchor_id}"', source,
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
                self.assertIn(f'"id":"{anchor_id}"', source,
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


class TestLanguageAndRegionPageRebuild(unittest.TestCase):
    """Language & region: atom rows, functional location editor kept."""

    def test_nexus_scaffold_with_self_rendered_title(self):
        source = _read("LanguageAndRegionPage.qml")
        self.assertIn("NexusPageBase {", source)
        self.assertIn('title: SpotlightCatalog.title("language-region")', source)

    def test_window_contract_surface_survives(self):
        source = _read("LanguageAndRegionPage.qml")
        for token in (
            "property var parentModal: null",
            "property bool presentationActive: false",
            "signal navigateRequested(string pageId)",
            "function closeChildWindows()",
            "property Item searchLeaf",
        ):
            self.assertIn(token, source, f"LanguageAndRegionPage lost window contract token: {token}")

    def test_search_anchor_ids_are_stable(self):
        source = _read("LanguageAndRegionPage.qml")
        for anchor_id in ANCHOR_IDS["LanguageAndRegionPage.qml"]:
            self.assertIn(f'"id":"{anchor_id}"', source,
                          f"anchor missing or rewritten: {anchor_id}")

    def test_atom_groups_present(self):
        source = _read("LanguageAndRegionPage.qml")
        for atom in ("PreferenceHeader", "PreferenceSelect", "ConnectedRect"):
            self.assertIn(atom, source, f"LanguageAndRegionPage must use the atom: {atom}")
        self.assertEqual(source.count("inputRegionService: PopupInputRegionService"), 4,
                         "every select row must register the popup input region")

    def test_business_owners_unchanged(self):
        source = _read("LanguageAndRegionPage.qml")
        for owner in (
            "UiPreferences.setLanguage",
            "UiPreferences.setWeatherTemperatureUnit",
            "UiPreferences.setSystemTemperatureUnit",
            "UiPreferences.setUseTwelveHourClock",
            "I18nService.supportedLanguages",
        ):
            self.assertIn(owner, source, f"business owner dropped: {owner}")
        # The real location editor stays, unlike Caelestia's placeholder.
        self.assertIn("LocationPicker {", source)
        self.assertIn("parentModal: root.parentModal", source)
        self.assertIn("WeatherService", _read("LocationPicker.qml"),
                      "the retained location editor keeps its weather owner")

    def test_legacy_chrome_stays_out(self):
        source = _read("LanguageAndRegionPage.qml")
        for token in LEGACY_VOCABULARY + ("SettingsSection", "SettingsRow", "StyledButtonGroup"):
            self.assertNotIn(token, source, f"legacy token re-entered LanguageAndRegionPage: {token}")


class TestDefaultAppsPageRebuild(unittest.TestCase):
    """Default applications: Caelestia DefaultRow shape on the select atom."""

    def test_nexus_scaffold_with_self_rendered_title(self):
        source = _read("DefaultAppsPage.qml")
        self.assertIn("NexusPageBase {", source)
        self.assertIn('title: SpotlightCatalog.title("default-apps")', source)

    def test_window_contract_surface_survives(self):
        source = _read("DefaultAppsPage.qml")
        for token in (
            "property var parentModal: null",
            "property bool presentationActive: false",
            "property Item searchLeaf",
        ):
            self.assertIn(token, source, f"DefaultAppsPage lost window contract token: {token}")

    def test_search_anchor_ids_are_stable(self):
        source = _read("DefaultAppsPage.qml")
        for anchor_id in ANCHOR_IDS["DefaultAppsPage.qml"]:
            self.assertIn(f'"id":"{anchor_id}"', source,
                          f"anchor missing or rewritten: {anchor_id}")

    def test_rows_reuse_the_select_atom(self):
        source = _read("DefaultAppsPage.qml")
        self.assertIn("component DefaultAppRow: PreferenceSelect", source,
                      "default-app rows must reuse the select atom (Caelestia DefaultRow shape)")
        self.assertIn("required property string roleId", source)
        self.assertIn("required property string roleTitle", source)
        self.assertIn("required property string roleIcon", source)
        self.assertIn("fallbackText:", source, "empty selections keep the Caelestia fallback")
        self.assertIn("inputRegionService: PopupInputRegionService", source)

    def test_business_owners_unchanged(self):
        source = _read("DefaultAppsPage.qml")
        for owner in (
            "DefaultApplicationsService.refresh()",
            "DefaultApplicationsService.stateFor(",
            "DefaultApplicationsService.setRole(",
            "DefaultApplicationsService.loading",
            "DefaultApplicationsService.busy",
            "DefaultApplicationsService.lastError",
            "DefaultApplicationsService.lastMessage",
        ):
            self.assertIn(owner, source, f"business owner dropped: {owner}")

    def test_legacy_chrome_stays_out(self):
        source = _read("DefaultAppsPage.qml")
        for token in LEGACY_VOCABULARY + ("SettingsSection", "SettingsRow", "ThemeIcon"):
            self.assertNotIn(token, source, f"legacy token re-entered DefaultAppsPage: {token}")


class TestSpotlightPageRebuild(unittest.TestCase):
    """Spotlight: selects and stepper atoms, clipboard lifecycle kept."""

    def test_nexus_scaffold_with_self_rendered_title(self):
        source = _read("SpotlightPage.qml")
        self.assertIn("NexusPageBase {", source)
        self.assertIn('title: SpotlightCatalog.title("spotlight")', source)

    def test_window_contract_surface_survives(self):
        source = _read("SpotlightPage.qml")
        for token in (
            "property var parentModal: null",
            "property bool presentationActive: false",
            "function closeChildWindows()",
            "property Item searchLeaf",
        ):
            self.assertIn(token, source, f"SpotlightPage lost window contract token: {token}")

    def test_search_anchor_ids_are_stable(self):
        source = _read("SpotlightPage.qml")
        for anchor_id in ANCHOR_IDS["SpotlightPage.qml"]:
            self.assertIn(f'"id":"{anchor_id}"', source,
                          f"anchor missing or rewritten: {anchor_id}")

    def test_atom_groups_present(self):
        source = _read("SpotlightPage.qml")
        for atom in ("PreferenceHeader", "PreferenceSelect", "PreferenceStepper"):
            self.assertIn(atom, source, f"SpotlightPage must use the atom: {atom}")
        self.assertEqual(source.count("inputRegionService: PopupInputRegionService"), 4,
                         "every select row must register the popup input region")

    def test_business_owners_unchanged(self):
        source = _read("SpotlightPage.qml")
        for owner in (
            "UiPreferences.setSpotlightAppStyle",
            "UiPreferences.setSpotlightAppOrder",
            "UiPreferences.setSpotlightSearchEngine",
            "UiPreferences.setSpotlightClipboardStyle",
            "UiPreferences.searchEngines",
            "ClipboardService.loadHistoryConfig()",
            "ClipboardService.setHistoryLimit",
            "ClipboardService.historyConfigLoaded",
        ):
            self.assertIn(owner, source, f"business owner dropped: {owner}")

    def test_legacy_chrome_stays_out(self):
        source = _read("SpotlightPage.qml")
        for token in LEGACY_VOCABULARY + ("SettingsSection", "SettingsRow"):
            self.assertNotIn(token, source, f"legacy token re-entered SpotlightPage: {token}")


class TestShellPageRebuild(unittest.TestCase):
    """Nyxuri Shell control plane: info/action/toggle atoms, owners intact."""

    def test_nexus_scaffold_with_self_rendered_title(self):
        source = _read("ShellPage.qml")
        self.assertIn("NexusPageBase {", source)
        self.assertIn('title: SpotlightCatalog.title("shell")', source)
        # Section headers live in the [ShellPage] translation section; an
        # explicit context keeps the runtime lookup and the i18n gate honest.
        for key in ("Modules & dependencies", "Session log", "Resource sampling", "Diagnostics & paths"):
            # Assembled from pieces: the i18n gate scans tests too and would
            # otherwise parse a template literal as a real call with key "{key}".
            call = "I18n." + "tr(" + '"' + key + '", "ShellPage")'
            self.assertIn(call, source, f"ShellPage header lost its translation context: {key}")

    def test_window_contract_surface_survives(self):
        source = _read("ShellPage.qml")
        for token in (
            "property var parentModal: null",
            "property bool presentationActive: false",
            "property Item searchLeaf",
        ):
            self.assertIn(token, source, f"ShellPage lost window contract token: {token}")

    def test_search_anchor_ids_are_stable(self):
        source = _read("ShellPage.qml")
        for anchor_id in ANCHOR_IDS["ShellPage.qml"]:
            self.assertIn(f'"id":"{anchor_id}"', source,
                          f"anchor missing or rewritten: {anchor_id}")

    def test_atom_groups_present(self):
        source = _read("ShellPage.qml")
        for atom in ("PreferenceHeader", "PreferenceInfo", "PreferenceToggle", "PreferenceAction"):
            self.assertIn(atom, source, f"ShellPage must use the atom: {atom}")
        # Unit switches ride the whole-row toggle atom, not raw switches.
        self.assertNotIn("StyledSwitch", source, "unit toggles must use PreferenceToggle")

    def test_business_owners_unchanged(self):
        source = _read("ShellPage.qml")
        for owner in (
            "ShellControlService.setPageMounted(true)",
            "ShellControlService.setPageMounted(false)",
            "ShellControlService.exportDiagnostics()",
            "UnitControlService.setUnit(",
            "UnitControlService.canToggle(",
            "UnitControlService.pendingUnitId",
            "StateProjection.isEnabled(",
            "NiriService.reconnect()",
            "PersonalizationConfig.setOverviewEnabled(",
            "UiPreferences.setControlPlaneResourceSampling(",
            "SystemMonitorService.retry()",
            "ApplicationService.openUrl(",
            "Paths.configHome",
        ):
            self.assertIn(owner, source, f"business owner dropped: {owner}")

    def test_legacy_chrome_stays_out(self):
        source = _read("ShellPage.qml")
        for token in LEGACY_VOCABULARY + ("SettingsSection", "SettingsRow", "GridLayout"):
            self.assertNotIn(token, source, f"legacy token re-entered ShellPage: {token}")


class TestGeneralBarPageRebuild(unittest.TestCase):
    """Bar: atom rows, drag-to-reorder fields kept as the custom shape."""

    def test_nexus_scaffold_with_self_rendered_title(self):
        source = _read("GeneralBarPage.qml")
        self.assertIn("NexusPageBase {", source)
        self.assertIn('title: SpotlightCatalog.title("bar")', source)

    def test_window_contract_surface_survives(self):
        source = _read("GeneralBarPage.qml")
        for token in (
            "property var parentModal: null",
            "property bool presentationActive: false",
            "property Item searchLeaf",
        ):
            self.assertIn(token, source, f"GeneralBarPage lost window contract token: {token}")

    def test_search_anchor_ids_are_stable(self):
        source = _read("GeneralBarPage.qml")
        for anchor_id in ANCHOR_IDS["GeneralBarPage.qml"]:
            self.assertIn('"id":"%s"' % anchor_id, source,
                          f"anchor missing or rewritten: {anchor_id}")

    def test_atom_groups_present(self):
        source = _read("GeneralBarPage.qml")
        for atom in ("PreferenceHeader", "PreferenceToggle", "PreferenceSelect", "ConnectedRect"):
            self.assertIn(atom, source, f"GeneralBarPage must use the atom: {atom}")
        self.assertEqual(source.count("inputRegionService: PopupInputRegionService"), 1,
                         "the screen-edge select must register the popup input region")

    def test_drag_fields_and_coordinators_survive(self):
        source = _read("GeneralBarPage.qml")
        self.assertEqual(source.count("SortableMultiSelectField {"), 3,
                         "two bar zones + the quick settings field stay drag-enabled")
        self.assertEqual(source.count("BarLayoutDragCoordinator {"), 2,
                         "one coordinator per drag surface (zones / quick settings)")
        self.assertIn("fields: [leadingField, trailingField]", source)
        self.assertIn("fields: [quickSettingsField]", source)
        # The overlay must not be a root child: NexusPageBase takes exactly
        # one content child, so both coordinators ride inside the content
        # wrapper that carries the column's implicit height.
        wrapper = source.index("implicitHeight: contentColumn.implicitHeight")
        self.assertIn("id: content", source[:wrapper],
                      "the content wrapper must precede the coordinators")
        self.assertGreater(source.index("BarLayoutDragCoordinator {"), wrapper,
                           "drag coordinators must live inside the content wrapper")

    def test_business_owners_unchanged(self):
        source = _read("GeneralBarPage.qml")
        for owner in (
            "PersonalizationConfig.setValue(\"barOverlay\"",
            "PersonalizationConfig.setBarPosition(",
            "PersonalizationConfig.setBarShowNames(",
            "PersonalizationConfig.setBarShowValues(",
            "PersonalizationConfig.toggleBarComponent(",
            "PersonalizationConfig.removeBarComponent(",
            "PersonalizationConfig.moveBarComponent(",
            "PersonalizationConfig.moveQuickSettingsComponent(",
            "PersonalizationConfig.toggleQuickSettingsComponent(",
            "PersonalizationConfig.removeQuickSettingsComponent(",
            "PersonalizationConfig.edgePositions",
            "PersonalizationConfig.barLeadingComponents",
            "PersonalizationConfig.barTrailingComponents",
            "PersonalizationConfig.quickSettingsComponents",
        ):
            self.assertIn(owner, source, f"business owner dropped: {owner}")

    def test_legacy_chrome_stays_out(self):
        source = _read("GeneralBarPage.qml")
        for token in LEGACY_VOCABULARY + ("SettingsSection", "SettingsRow", "StyledSwitch",
                                          "EdgePositionSelector"):
            self.assertNotIn(token, source, f"legacy token re-entered GeneralBarPage: {token}")


class TestDockPageRebuild(unittest.TestCase):
    """Dock: atom rows, first-run integration prompt kept above the groups."""

    def test_nexus_scaffold_with_self_rendered_title(self):
        source = _read("DockPage.qml")
        self.assertIn("NexusPageBase {", source)
        self.assertIn('title: SpotlightCatalog.title("dock")', source)

    def test_window_contract_surface_survives(self):
        source = _read("DockPage.qml")
        for token in (
            "property var parentModal: null",
            "property bool presentationActive: false",
            "property Item searchLeaf",
        ):
            self.assertIn(token, source, f"DockPage lost window contract token: {token}")

    def test_search_anchor_ids_are_stable(self):
        source = _read("DockPage.qml")
        for anchor_id in ANCHOR_IDS["DockPage.qml"]:
            self.assertIn('"id":"%s"' % anchor_id, source,
                          f"anchor missing or rewritten: {anchor_id}")

    def test_atom_groups_present(self):
        source = _read("DockPage.qml")
        for atom in ("PreferenceHeader", "PreferenceToggle", "PreferenceSlider", "PreferenceSelect"):
            self.assertIn(atom, source, f"DockPage must use the atom: {atom}")
        self.assertEqual(source.count("inputRegionService: PopupInputRegionService"), 3,
                         "edge / surface style / minimize animation selects register input regions")

    def test_setup_prompt_and_busy_semantics_survive(self):
        source = _read("DockPage.qml")
        self.assertIn("NiriSetupPrompt {", source, "the first-run integration prompt stays")
        self.assertIn('NiriConfigService.setup("minimize-animation")', source)
        self.assertIn('NiriConfigService.setMinimizeEffect(', source)
        # The busy state folded into the subtext instead of a side spinner.
        self.assertIn('NiriConfigService.activeFeature === "minimize-animation"', source)

    def test_business_owners_unchanged(self):
        source = _read("DockPage.qml")
        for owner in (
            'DockService.setOption("position"',
            'DockService.setOption("iconSize"',
            'DockService.setOption("magnification"',
            'DockService.setOption("magnificationScale"',
            'DockService.setOption("surfaceStyle"',
            'DockService.setOption("autoHide"',
            'DockService.setOption("launchBounce"',
            'DockService.setOption("showIndicators"',
            'DockService.setOption("showRecent"',
            'DockService.setOption("contextPinning"',
            'DockService.setOption("showThumbnails"',
            'DockService.setOption("previewSize"',
            "DockService.configError",
            "DockService.supportsThumbnails",
            "DockService.supportsMinimizeEffects",
        ):
            self.assertIn(owner, source, f"business owner dropped: {owner}")

    def test_legacy_chrome_stays_out(self):
        source = _read("DockPage.qml")
        for token in LEGACY_VOCABULARY + ("SettingsSection", "SettingsRow", "StyledSwitch",
                                          "StyledButtonGroup", "GeneralSliderSetting",
                                          "InlineBusyIndicator"):
            self.assertNotIn(token, source, f"legacy token re-entered DockPage: {token}")


class TestGeneralSidebarPageRebuild(unittest.TestCase):
    """Sidebars: atom rows, layout twin-picker and card grid kept, sampling
    consumers armed only while the page is presented."""

    def test_nexus_scaffold_with_self_rendered_title(self):
        source = _read("GeneralSidebarPage.qml")
        self.assertIn("NexusPageBase {", source)
        self.assertIn('title: SpotlightCatalog.title("sidebar")', source)

    def test_window_contract_surface_survives(self):
        source = _read("GeneralSidebarPage.qml")
        for token in (
            "property var parentModal: null",
            "property bool presentationActive: false",
            "property Item searchLeaf",
        ):
            self.assertIn(token, source, f"GeneralSidebarPage lost window contract token: {token}")

    def test_search_anchor_ids_are_stable(self):
        source = _read("GeneralSidebarPage.qml")
        for anchor_id in ANCHOR_IDS["GeneralSidebarPage.qml"]:
            self.assertIn('"id":"%s"' % anchor_id, source,
                          f"anchor missing or rewritten: {anchor_id}")

    def test_atom_groups_present(self):
        source = _read("GeneralSidebarPage.qml")
        for atom in ("PreferenceHeader", "PreferenceToggle", "PreferenceSelect",
                     "PreferenceStepper", "PreferenceInput"):
            self.assertIn(atom, source, f"GeneralSidebarPage must use the atom: {atom}")
        self.assertEqual(source.count("inputRegionService: PopupInputRegionService"), 10,
                         "ten select rows must register the popup input region")

    def test_sampling_consumer_lifecycle_survives(self):
        source = _read("GeneralSidebarPage.qml")
        self.assertIn('SystemMonitorService.setConsumerModules("general-sidebar-settings"', source)
        self.assertIn('SystemMonitorService.clearConsumer("general-sidebar-settings")', source)
        self.assertIn("onPresentationActiveChanged:", source,
                      "arming must track presentation, not just construction")

    def test_cookie_block_dims_like_before(self):
        source = _read("GeneralSidebarPage.qml")
        self.assertEqual(source.count("root.cookieClockActive ? 1 : 0.42"), 9,
                         "every cookie sub-row keeps the 42% dim while digital is active")
        self.assertIn('UiPreferences.setSidebarCookieSides(', source)
        self.assertIn('UiPreferences.setSidebarCookieDialStyle(', source)
        self.assertIn('UiPreferences.setSidebarCookieHourHandStyle(', source)
        self.assertIn('UiPreferences.setSidebarCookieMinuteHandStyle(', source)
        self.assertIn('UiPreferences.setSidebarCookieSecondHandStyle(', source)
        self.assertIn('UiPreferences.setSidebarCookieDateStyle(', source)

    def test_semantic_pickers_survive_as_custom_shapes(self):
        source = _read("GeneralSidebarPage.qml")
        # The layout block is one card holding twin pickers bound to the same
        # backing value (mode + placement presets) — no atom has this shape.
        self.assertEqual(source.count("SystemCardService.setGlobalDesktopLayoutMode(value)"), 2)
        self.assertIn("GridLayout", source, "the two-column card grid stays")
        self.assertIn("SystemCardService.setCardEnabled(", source)

    def test_business_owners_unchanged(self):
        source = _read("GeneralSidebarPage.qml")
        for owner in (
            "PersonalizationConfig.setDashboardSidebarSide(",
            "PersonalizationConfig.setQuickSettingsSidebarSide(",
            "PersonalizationConfig.setKeepSidebarsLoaded(",
            "PersonalizationConfig.setDesktopCardGridSnapEnabled(",
            "PersonalizationConfig.setDesktopCardGridVisibleWhileDragging(",
            "UiPreferences.setSidebarClockStyle(",
            "UiPreferences.setSidebarCookieConstantlyRotate(",
            "UiPreferences.setSidebarCookieHourMarks(",
            "UiPreferences.setSidebarCookieTimeIndicators(",
            "UiPreferences.setSystemMonitorGpuId(",
            "UiPreferences.setSystemMonitorIntervalMs(",
            "UiPreferences.setStorageCapacityDiskDevice(",
            "SystemMonitorService.gpus",
            "SystemMonitorService.disks",
        ):
            self.assertIn(owner, source, f"business owner dropped: {owner}")

    def test_legacy_chrome_stays_out(self):
        source = _read("GeneralSidebarPage.qml")
        for token in LEGACY_VOCABULARY + ("SettingsSection", "SettingsRow", "StyledSwitch",
                                          "MaterialFilledTextField", "MaterialStepper"):
            self.assertNotIn(token, source, f"legacy token re-entered GeneralSidebarPage: {token}")


class TestKeystonePageRebuild(unittest.TestCase):
    """Keystone: overview on the Nexus scaffold, routed subpage kept, drag
    fields and directory pickers preserved as custom shapes."""

    def test_shell_routing_survives(self):
        source = _read("KeystonePage.qml")
        self.assertIn("readonly property bool rendersPageTitle: true", source)
        self.assertIn("function openSearchPath(path, serial)", source)
        self.assertIn("currentSection === \"overview\" ? overviewPage.flickable", source)
        self.assertIn("function closeChildWindows()", source)
        self.assertIn("directoryPicker.dismiss()", source)

    def test_overview_is_a_nexus_page(self):
        source = _read("KeystonePage.qml")
        self.assertIn("NexusPageBase {", source)
        self.assertIn('title: SpotlightCatalog.title("keystone")', source)

    def test_search_anchor_ids_are_stable(self):
        source = _read("KeystonePage.qml")
        for anchor_id in ANCHOR_IDS["KeystonePage.qml"]:
            self.assertIn('"id":"%s"' % anchor_id, source,
                          f"anchor missing or rewritten: {anchor_id}")

    def test_atom_groups_present(self):
        source = _read("KeystonePage.qml")
        for atom in ("PreferenceHeader", "PreferenceToggle", "PreferenceSelect",
                     "PreferenceSlider", "PreferenceAction", "ConnectedRect"):
            self.assertIn(atom, source, f"KeystonePage must use the atom: {atom}")
        self.assertEqual(source.count("inputRegionService: PopupInputRegionService"), 9,
                         "nine select rows must register the popup input region")

    def test_drag_fields_and_directory_pickers_survive(self):
        source = _read("KeystonePage.qml")
        self.assertEqual(source.count("SortableMultiSelectField {"), 2,
                         "long-bar leading/trailing zones stay drag-enabled")
        self.assertIn("fields: [longLeadingField, longTrailingField]", source)
        self.assertIn("moveKeystoneLongItem(", source)
        # The coordinator must ride inside the overview content wrapper, not
        # on the shell root.
        wrapper = source.index("implicitHeight: overviewColumn.implicitHeight")
        self.assertGreater(source.index("BarLayoutDragCoordinator {"), wrapper,
                           "the drag overlay must live inside the content wrapper")
        self.assertIn("FilePickerWindow {", source)
        self.assertIn("openDirectoryPicker(", source)
        self.assertIn("UiPreferences.setRecordingDirectory(", source)
        self.assertIn("RecordingDirectoryField", source)

    def test_subpage_chrome_moves_into_the_subpage(self):
        source = _read("KeystonePage.qml")
        self.assertNotIn("GeneralSubpageHeader", source,
                         "the subpage renders its own NexusPageBase back header")
        self.assertIn("backRequested.connect(root.showOverview)", source,
                      "the shell wires the subpage back arrow to the overview")
        self.assertIn('root.openSection("horizontal-clock")', source)

    def test_business_owners_unchanged(self):
        source = _read("KeystonePage.qml")
        for owner in (
            'PersonalizationConfig.setValue("keystoneOverlay"',
            "PersonalizationConfig.setKeystoneStyle(",
            "PersonalizationConfig.setKeystonePosition(",
            'PersonalizationConfig.setKeystoneAction("hover"',
            'PersonalizationConfig.setKeystoneAction("left"',
            'PersonalizationConfig.setKeystoneAction("middle"',
            "PersonalizationConfig.setKeystoneHoverOpenDelay(",
            "PersonalizationConfig.setKeystoneHoverCloseDelay(",
            "PersonalizationConfig.setKeystoneMediaProgressStyle(",
            "PersonalizationConfig.setKeystoneMediaCoverStyle(",
            "PersonalizationConfig.setKeystoneMediaColorStyle(",
            "PersonalizationConfig.setKeystoneLongShowNames(",
            "PersonalizationConfig.setKeystoneLongShowMonitorValues(",
            "PersonalizationConfig.setKeystoneLongShowValues(",
            "PersonalizationConfig.toggleKeystoneLongItem(",
            "PersonalizationConfig.removeKeystoneLongItem(",
            "PersonalizationConfig.setKeystoneCapsLockOsd(",
            "PersonalizationConfig.setKeystoneNumLockOsd(",
            "PersonalizationConfig.setKeystoneKeyholeCard(",
            "PersonalizationConfig.setKeystoneHideDate(",
            "KeyboardLockService.available",
        ):
            self.assertIn(owner, source, f"business owner dropped: {owner}")

    def test_legacy_chrome_stays_out(self):
        source = _read("KeystonePage.qml")
        for token in LEGACY_VOCABULARY + ("SettingsSection", "SettingsRow", "StyledSwitch",
                                          "KeystoneSection", "SearchSelectSettingRow",
                                          "GeneralSliderSetting", "EdgePositionSelector"):
            self.assertNotIn(token, source, f"legacy token re-entered KeystonePage: {token}")


class TestHorizontalClockPageRebuild(unittest.TestCase):
    """Horizontal clock: subpage scaffold, slider commit semantics, digit
    picker kept as the segmented semantic picker."""

    def test_nexus_subpage_scaffold(self):
        source = _read("HorizontalClockPage.qml")
        self.assertIn("NexusPageBase {", source)
        self.assertIn('title: SpotlightCatalog.title("keystone.horizontal-clock")', source)
        self.assertIn("isSubPage: true", source)
        self.assertIn("property Item searchLeaf", source)

    def test_search_anchor_ids_are_stable(self):
        source = _read("HorizontalClockPage.qml")
        for anchor_id in ANCHOR_IDS["HorizontalClockPage.qml"]:
            self.assertIn('"id":"%s"' % anchor_id, source,
                          f"anchor missing or rewritten: {anchor_id}")

    def test_slider_rows_keep_commit_semantics(self):
        source = _read("HorizontalClockPage.qml")
        self.assertEqual(source.count("PreferenceSlider {"), 10,
                         "seven font axes + three digit offsets ride the slider atom")
        self.assertEqual(source.count("onCommitted:"), 10,
                         "every axis slider must persist on commit, not on every tick")
        self.assertGreaterEqual(source.count("onMoved:"), 10)

    def test_semantic_pickers_survive(self):
        source = _read("HorizontalClockPage.qml")
        self.assertIn("StyledButtonGroup {", source, "the live-digit picker stays segmented")
        self.assertIn("HorizontalClockPreview {", source)
        self.assertIn("MaterialTextField {", source, "the custom hex field stays")

    def test_business_owners_unchanged(self):
        source = _read("HorizontalClockPage.qml")
        for owner in (
            "PersonalizationConfig.setHorizontalClockFontSize(",
            'PersonalizationConfig.setHorizontalClockAxis("wght"',
            'PersonalizationConfig.setHorizontalClockAxis("wdth"',
            'PersonalizationConfig.setHorizontalClockAxis("opsz"',
            'PersonalizationConfig.setHorizontalClockAxis("GRAD"',
            'PersonalizationConfig.setHorizontalClockAxis("ROND"',
            'PersonalizationConfig.setHorizontalClockAxis("slnt"',
            "PersonalizationConfig.setHorizontalClockDigitColor(",
            "PersonalizationConfig.setHorizontalClockDigitValue(",
            "PersonalizationConfig.setKeystoneHideDate(",
            "PersonalizationConfig.horizontalClockAxes",
        ):
            self.assertIn(owner, source, f"business owner dropped: {owner}")

    def test_legacy_chrome_stays_out(self):
        source = _read("HorizontalClockPage.qml")
        for token in LEGACY_VOCABULARY + ("SettingsSection", "SettingsRow", "StyledSwitch",
                                          "KeystoneSection", "ClockSliderSetting"):
            self.assertNotIn(token, source, f"legacy token re-entered HorizontalClockPage: {token}")


if __name__ == "__main__":
    unittest.main()
