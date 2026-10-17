import QtQuick
import qs.app
import qs.app.services
// Unit module warm-up (see note below): registers every synthesized
// qs.modules.* import graph at engine startup, before any Loader fires.
import qs.modules.bar
import qs.modules.desktopcards
import qs.modules.dock
import qs.modules.keystone
import qs.modules.launcher
import qs.modules.lock
import qs.modules.notifications
import qs.modules.regionselector
import qs.modules.session
import qs.modules.settings
import qs.modules.sidebars
import qs.modules.wallpaper

// SlotHost — the microkernel's geometric slot host (unit-model.md §6).
//
// WHY THE STATIC IMPORTS: Quickshell 0.3.2's qs-import resolution is
// unreliable for imports processed inside Loader-loaded components at cold
// start — losers report nondeterministic "module not installed" /
// "X is not a type" and their whole unit dies (run-to-run shifting failure
// sets, cache-clearing does not help). Registering the module graphs
// statically here restores the deterministic import order the pre-KM4
// static AppShell had, while instantiation stays purely Loader-driven:
// these imports never create a unit component. Disabled units still get
// Loader.active = false — zero instantiation, zero windows, zero retained
// memory; the parse-only cost of warm registration is a documented 0.3.2
// constraint, revisited on quickshell upgrade.
// Data-driven: every Shell unit loads through exactly one Loader keyed by
// StateProjection; no unit is ever instantiated here by name. A disabled
// unit keeps Loader.active false — zero file reads, zero instantiation,
// zero retained memory; re-enabling rebuilds the domain fresh.
//
// Slot arbitration (host-owned; the only place units may conflict):
// - lock: a held session lock is never torn down mid-lock. An `off` that
//   arrives while locked keeps the unit loaded until the lock releases
//   (shell AGENTS: 锁屏中禁止销毁安全锁).
// - notifications: the popup:notification slot belongs to the keystone
//   island whenever keystone is enabled; the standalone popup host loads
//   only when keystone is off.
Item {
    id: root

    // Cross-unit dependency bridge point (four-layer rule: 跨模块协调由 app
    // 的窄接口完成). Emitted whenever a unit's root item comes alive.
    signal unitLoaded(string unitId, var item)

    function slotActive(unit) {
        if (!StateProjection.isEnabled(unit.id)) {
            return unit.id === "lock" && ActionGateway.lockEngaged;
        }
        if (unit.id === "notifications" && StateProjection.isEnabled("keystone"))
            return false;
        return true;
    }

    Repeater {
        model: UnitCatalog.units

        delegate: Loader {
            required property var modelData

            active: root.slotActive(modelData)
            source: modelData.source
            onLoaded: root.unitLoaded(modelData.id, item)
        }
    }
}
