import Quickshell
import Quickshell.Io
import QtQuick
import "components"

Scope {
    id: root
    
    property bool launcherOpen: false
    property bool powerMenuOpen: false
    property bool calendarOpen: false
    property bool keybindsOpen: false
    property bool clipboardOpen: false
    property bool notificationsOpen: false
    property bool mediaOpen: false
    property bool controlCenterOpen: false

    Process {
        id: volumeProc
    }

    function closeAll() {
        launcherOpen = false;
        powerMenuOpen = false;
        calendarOpen = false;
        keybindsOpen = false;
        clipboardOpen = false;
        notificationsOpen = false;
        mediaOpen = false;
        controlCenterOpen = false;
    }

    IpcHandler {
        target: "drawer"
        function toggle(): void {
            let state = root.launcherOpen;
            root.closeAll();
            root.launcherOpen = !state;
        }
    }

    IpcHandler {
        target: "powermenu"
        function toggle(): void {
            let state = root.powerMenuOpen;
            root.closeAll();
            root.powerMenuOpen = !state;
        }
    }

    IpcHandler {
        target: "keybinds"
        function toggle(): void {
            let state = root.keybindsOpen;
            root.closeAll();
            root.keybindsOpen = !state;
        }
    }

    IpcHandler {
        target: "notifications"
        function toggle(): void {
            let state = root.notificationsOpen;
            root.closeAll();
            root.notificationsOpen = !state;
        }
    }

    IpcHandler {
        target: "media"
        function toggle(): void {
            let state = root.mediaOpen;
            root.closeAll();
            root.mediaOpen = !state;
        }
    }

    IpcHandler {
        target: "clipboard"
        function toggle(): void {
            let state = root.clipboardOpen;
            root.closeAll();
            root.clipboardOpen = !state;
        }
    }

    IpcHandler {
        target: "calendar"
        function toggle(): void {
            let state = root.calendarOpen;
            root.closeAll();
            root.calendarOpen = !state;
        }
    }

    IpcHandler {
        target: "controlcenter"
        function toggle(): void {
            let state = root.controlCenterOpen;
            root.closeAll();
            root.controlCenterOpen = !state;
        }
    }

    IpcHandler {
        target: "volume"
        function up(): void {
            volumeProc.exec(["wpctl", "set-volume", "-l", "1.5", "@DEFAULT_AUDIO_SINK@", "5%+"]);
        }
        function down(): void {
            volumeProc.exec(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"]);
        }
        function mute(): void {
            volumeProc.exec(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"]);
        }
        function change(action: string): void {
            if (action === "up") up();
            else if (action === "down") down();
            else if (action === "mute") mute();
        }
    }

    Variants {
        model: Quickshell.screens

        delegate: Item {
            required property var modelData

            TopBar { targetScreen: modelData; rootScope: root }
            BottomDock { targetScreen: modelData; rootScope: root }
            Launcher { targetScreen: modelData; rootScope: root }
            PowerMenu { targetScreen: modelData; rootScope: root }
            CalendarDropdown { targetScreen: modelData; rootScope: root }
            ClipboardMenu { targetScreen: modelData; rootScope: root }
            KeybindsMenu { screen: modelData; rootScope: root }
            Notifications { targetScreen: modelData; rootScope: root }
            MediaMenu { targetScreen: modelData; rootScope: root }
            ControlCenter { targetScreen: modelData; rootScope: root }
        }
    }
}
