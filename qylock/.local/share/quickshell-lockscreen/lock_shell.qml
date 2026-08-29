import QtQuick
import Quickshell
import Quickshell.Wayland
import QtMultimedia
import "./shim"


ShellRoot {
    id: shellRoot

    property string activeTheme: Quickshell.env("QS_THEME") || "material-you"
    property string themePath: Quickshell.env("QS_THEME_PATH") || (Quickshell.shellDir + "/themes_link/" + activeTheme)

    readonly property var sddm: sddmShim.sddm
    readonly property var config: sddmShim.config
    readonly property var userModel: sddmShim.userModel
    readonly property var sessionModel: sddmShim.sessionModel
    readonly property bool isWayland: Quickshell.env("XDG_SESSION_TYPE") === "wayland"
    property bool authenticated: false
    property bool sessionLocked: true
    property bool isTesting: Quickshell.env("QS_TESTING") === "1"

    SddmShim {
        id: sddmShim
        themePath: shellRoot.themePath
    }

    function injectThemeContext(item) {
        if (!item)
            return;
        // Dynamic props so SDDM-style themes can resolve bare `sddm` / models
        item.sddm = shellRoot.sddm;
        item.userModel = shellRoot.userModel;
        item.sessionModel = shellRoot.sessionModel;
        item.config = shellRoot.config;
        item.forceActiveFocus();
    }

    Connections {
        target: sddmShim.sddm
        function onLoginSucceeded() {
            shellRoot.authenticated = true

            if (Quickshell.env("XDG_CURRENT_DESKTOP") === "Hyprland" || Quickshell.env("HYPRLAND_INSTANCE_SIGNATURE") !== "") {
                Quickshell.execDetached(["hyprctl", "keyword", "misc:allow_session_lock_restore", "1"]);
            }
            Quickshell.execDetached(["loginctl", "unlock-session"]);

            let delay = 100;
            if (activeTheme.includes("clockwork") && sddmShim.config.enableWindup === "true") {
                delay = 500;
            }
            quitTimer.interval = delay;
            quitTimer.start()
        }

        function onPowerActionRequested(action) {
            // Release session lock first so Hyprland does not flash "lockscreen died"
            shellRoot.authenticated = true
            shellRoot.sessionLocked = false
            powerActionTimer.action = action
            powerActionTimer.start()
        }
    }

    Timer {
        id: quitTimer
        interval: 3000
        onTriggered: {
            shellRoot.sessionLocked = false
            Qt.quit()
        }
    }

    Timer {
        id: powerActionTimer
        property string action: ""
        interval: 150
        repeat: false
        onTriggered: {
            const cmd = ({
                reboot: "if [ -d /run/systemd/system ]; then systemctl reboot; else loginctl reboot; fi",
                poweroff: "if [ -d /run/systemd/system ]; then systemctl poweroff; else loginctl poweroff; fi",
                suspend: "if [ -d /run/systemd/system ]; then systemctl suspend; else loginctl suspend; fi"
            })[action]

            if (cmd)
                Quickshell.execDetached(["bash", "-c", cmd])

            // For suspend, quit lock after requesting sleep so we don't leave a dead lock
            if (action === "suspend")
                Qt.quit()
        }
    }

    Component {
        id: themeComponent
        Loader {
            anchors.fill: parent
            source: "file://" + shellRoot.themePath + "/Main.qml"

            onLoaded: shellRoot.injectThemeContext(item)
            onStatusChanged: {
                if (status === Loader.Error) {
                    console.error("FAILED to load theme:", source)
                }
            }
        }
    }

    Loader {
        id: waylandLoader
        active: shellRoot.isWayland
        sourceComponent: Component {
            WlSessionLock {
                id: lock
                locked: shellRoot.sessionLocked
                surface: Component {
                    WlSessionLockSurface {
                        color: "black"

                        PinchHandler { target: null }
                        WheelHandler { target: null }

                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.AllButtons
                            hoverEnabled: true
                            onWheel: (wheel) => { wheel.accepted = true }
                        }

                        Loader {
                            anchors.fill: parent
                            sourceComponent: themeComponent
                        }
                    }
                }
            }
        }
    }

    Loader {
        id: x11Loader
        active: !shellRoot.isWayland
        sourceComponent: Component {
            Variants {
                model: Quickshell.screens
                delegate: Window {
                    id: window
                    required property var modelData
                    screen: modelData
                    width: isTesting ? 1280 : screen.width
                    height: isTesting ? 720 : screen.height
                    visible: shellRoot.sessionLocked
                    visibility: isTesting ? Window.Windowed : Window.FullScreen

                    onClosing: (close) => {
                        close.accepted = shellRoot.authenticated || shellRoot.isTesting;
                    }

                    flags: Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.MaximizeUsingFullscreenGeometryHint
                    color: "black"

                    Loader {
                        anchors.fill: parent
                        sourceComponent: themeComponent
                    }
                }
            }
        }
    }
}
