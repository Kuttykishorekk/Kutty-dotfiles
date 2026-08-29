pragma ComponentBehavior: Bound

import "lock"
import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Services.UPower
import Caelestia.Config
import Caelestia.Services
import qs.services

Scope {
    id: root

    required property Lock lock
    readonly property bool hasPlayer: Players.list.some(p => p.isPlaying)
    readonly property bool isCharging: !UPower.onBattery
    readonly property bool enabled: {
        if (GlobalConfig.general.idle.inhibitWhenAudio && hasPlayer)
            return false;
        if (GlobalConfig.general.idle.inhibitWhenCharging && isCharging)
            return false;
        return true;
    }

    function handleIdleAction(action: var): void {
        if (!action)
            return;

        // Use qylock for session lock — never Caelestia's WlSessionLock
        if (action === "lock")
            Quickshell.execDetached(["/home/kutty/.local/bin/qylock"]);
        else if (action === "unlock")
            Quickshell.execDetached(["loginctl", "unlock-session"]);
        else if (typeof action === "string")
            Hypr.dispatch(Hypr.usingLua && ["dpms off", "dpms on"].includes(action) ? `hl.dsp.dpms({ action = "${action === "dpms off" ? "disable" : "enable"}" })` : action);
        else if (!SessionManager.exec(action))
            Quickshell.execDetached(action);
    }

    Connections {
        function onAboutToSleep(): void {
            if (GlobalConfig.general.idle.lockBeforeSleep)
                Quickshell.execDetached(["/home/kutty/.local/bin/qylock"]);
        }

        function onLockRequested(): void {
            // hypridle already runs qylock on loginctl lock-session;
            // do not race with Caelestia's own session lock.
        }

        function onUnlockRequested(): void {
            // Only clear Caelestia's unused lock object; qylock handles real unlock via PAM.
            root.lock.lock.unlock();
        }

        target: SessionManager
    }

    Variants {
        model: GlobalConfig.general.idle.timeouts

        IdleMonitor {
            required property var modelData

            enabled: {
                if (!root.enabled || !(modelData.enabled ?? true))
                    return false;
                if (modelData.inhibitWhenAudio && root.hasPlayer)
                    return false;
                if (modelData.inhibitWhenCharging && root.isCharging)
                    return false;
                return true;
            }
            timeout: modelData.timeout
            respectInhibitors: modelData.respectInhibitors ?? true
            onIsIdleChanged: root.handleIdleAction(isIdle ? modelData.idleAction : modelData.returnAction)
        }
    }
}
