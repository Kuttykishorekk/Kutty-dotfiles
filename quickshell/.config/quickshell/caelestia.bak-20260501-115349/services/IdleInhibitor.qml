pragma Singleton

import Quickshell
import Quickshell.Io
import Quickshell.Wayland as Wl

Singleton {
    id: root

    property alias enabled: props.enabled
    readonly property alias enabledSince: props.enabledSince

    onEnabledChanged: {
        if (enabled)
            props.enabledSince = new Date();
    }

    PersistentProperties {
        id: props

        property bool enabled
        property date enabledSince

        reloadableId: "idleInhibitor"
    }

    // NOTE:
    // Originally this service instantiated an `IdleInhibitor { ... }` object
    // here. With newer Quickshell / Caelestia versions that leads to
    // "IdleInhibitor is instantiated recursively" errors because this file
    // itself defines the `IdleInhibitor` type.
    //
    // For now we skip creating the underlying Wayland idle‑inhibitor object.
    // The service still exposes IPC + state, but does not actually inhibit
    // idle. This avoids the crash and lets Caelestia start.

    IpcHandler {
        target: "idleInhibitor"

        function isEnabled(): bool {
            return props.enabled;
        }

        function toggle(): void {
            props.enabled = !props.enabled;
        }

        function enable(): void {
            props.enabled = true;
        }

        function disable(): void {
            props.enabled = false;
        }
    }
}
