import QtQuick
import qs.app
import qs.app.services
// Unit module warm-up (see note below): registers every synthesized
// qs.units.* import graph at engine startup, before any Loader fires.
import qs.units.bar
import qs.units.desktopcards
import qs.units.dock
import qs.units.keystone
import qs.units.launcher
import qs.units.lock
import qs.units.notifications
import qs.units.regionselector
import qs.units.session
import qs.units.settings
import qs.units.sidebars
import qs.units.wallpaper

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
        id: slotRepeater

        model: UnitCatalog.units

        delegate: Loader {
            id: delegate

            required property var modelData
            // Self-heal gate (Quickshell 0.3.2): a unit can fail its cold
            // compile nondeterministically and come up as a silent null
            // item. The host retries such units twice before giving up.
            property bool suppressed: false

            active: root.slotActive(modelData) && !suppressed
            source: modelData.source
            onLoaded: root.unitLoaded(modelData.id, item)
        }
    }

    // Compile-failure self-heal: "the ledger says loaded but the item is
    // null" means the unit's QML died in compilation. Two bounded retry
    // passes (fresh compile, cache already cleared at launch); every retry
    // is logged loudly — silent missing UI is the failure mode that ate a
    // debugging afternoon.
    property int _healPasses: 0

    Timer {
        id: healTimer

        interval: 4000
        repeat: true
        running: true

        onTriggered: {
            root._healPasses += 1;
            let retried = 0;
            for (let i = 0; i < UnitCatalog.units.length; i++) {
                const unit = UnitCatalog.units[i];
                const loader = slotRepeater.itemAt(i);
                if (!loader || loader.suppressed)
                    continue;
                if (!root.slotActive(unit) || loader.item !== null)
                    continue;
                retried += 1;
                LogService.error("host", "unit shell." + unit.id
                                 + " enabled but compiled empty — reloading (pass " + root._healPasses
                                 + "/2)");
                loader.suppressed = true;
            }
            if (retried > 0) {
                releaseSuppressed.restart();
            } else {
                stop();
            }
        }
    }

    Timer {
        id: releaseSuppressed

        interval: 250
        repeat: false
        onTriggered: {
            for (let i = 0; i < UnitCatalog.units.length; i++) {
                const loader = slotRepeater.itemAt(i);
                if (loader)
                    loader.suppressed = false;
            }
        }
    }

    Component.onDestruction: {
        healTimer.stop();
        releaseSuppressed.stop();
    }
}
