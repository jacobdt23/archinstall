import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import QtQuick.Layouts

PanelWindow {
    id: welcomeWindow
    required property var targetScreen
    required property var rootScope

    screen: targetScreen
    anchors { top: true; bottom: true; left: true; right: true }

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
    exclusionMode: ExclusionMode.Ignore
    visible: rootScope.welcomeOpen
    color: "transparent"

    property int activeTab: 0 // 0 = Essential Apps, 1 = Keybinds Cheat Sheet
    property bool autostartEnabled: true

    Process { id: appRunner }
    Process { id: toggleAutostartProc }

    Process {
        id: checkAutostartProc
        command: ["sh", "-c", "test -f ~/.config/jacob-welcome-disabled && echo disabled || echo enabled"]
        running: true
        stdout: SplitParser {
            onRead: data => {
                if (data.trim() === "disabled") {
                    welcomeWindow.autostartEnabled = false;
                } else {
                    welcomeWindow.autostartEnabled = true;
                    rootScope.welcomeOpen = true;
                }
            }
        }
    }

    ListModel {
        id: essentialAppsModel
        Component.onCompleted: {
            let apps = [
                {
                    title: "Install System (Calamares)",
                    subtitle: "Graphical Btrfs/GPT/MBR OS Installer",
                    icon: "file:///usr/share/icons/hicolor/scalable/apps/calamares.svg",
                    accent: "#7aa2f7",
                    cmd: "/usr/local/bin/launch-calamares"
                },
                {
                    title: "Timeshift Btrfs Snapshots",
                    subtitle: "Create & Restore Bootable GRUB Snapshots",
                    icon: "file:///usr/share/icons/hicolor/128x128/apps/timeshift.png",
                    accent: "#f7768e",
                    cmd: "/usr/local/bin/timeshift-launcher"
                },
                {
                    title: "Firefox Web Browser",
                    subtitle: "Fast, Private Web Browser",
                    icon: "file:///usr/share/icons/hicolor/256x256/apps/firefox.png",
                    accent: "#ff9e64",
                    cmd: "firefox"
                },
                {
                    title: "Kitty Terminal",
                    subtitle: "GPU-Accelerated Terminal Emulator",
                    icon: "file:///usr/share/icons/hicolor/256x256/apps/kitty.png",
                    accent: "#bb9af7",
                    cmd: "kitty"
                },
                {
                    title: "Thunar File Manager",
                    subtitle: "Browse Disks, Folders & Archives",
                    icon: "file:///usr/share/icons/hicolor/128x128/apps/org.xfce.thunar.png",
                    accent: "#7dcfff",
                    cmd: "thunar"
                },
                {
                    title: "Audio Mixer (Pavucontrol)",
                    subtitle: "Configure Speakers, Headsets & Mic",
                    icon: "file:///usr/share/icons/hicolor/scalable/apps/org.pulseaudio.pavucontrol.svg",
                    accent: "#9ece6a",
                    cmd: "pavucontrol"
                },
                {
                    title: "Bluetooth Manager",
                    subtitle: "Pair Controllers, Audio & Devices",
                    icon: "file:///usr/share/icons/hicolor/256x256/apps/blueman.png",
                    accent: "#7aa2f7",
                    cmd: "blueman-manager"
                },
                {
                    title: "Network & Wi-Fi Setup",
                    subtitle: "Connect to Wi-Fi, Ethernet & VPN",
                    icon: "file:///usr/share/icons/hicolor/scalable/apps/nm-device-wired.svg",
                    accent: "#e0af68",
                    cmd: "nm-connection-editor || kitty -e nmtui"
                },
                {
                    title: "OBS Studio",
                    subtitle: "Screen Recording & Live Streaming",
                    icon: "file:///usr/share/icons/hicolor/256x256/apps/com.obsproject.Studio.png",
                    accent: "#c0caf5",
                    cmd: "obs"
                },
                {
                    title: "System Monitor (btop++)",
                    subtitle: "Live CPU, Memory, Disk & Process Viewer",
                    icon: "file:///usr/share/icons/hicolor/scalable/apps/btop.svg",
                    accent: "#f7768e",
                    cmd: "kitty -e btop"
                }
            ];
            for (let i = 0; i < apps.length; i++) {
                essentialAppsModel.append(apps[i]);
            }
        }
    }

    ListModel {
        id: cheatSheetModel
        Component.onCompleted: {
            let binds = [
                { key: "SUPER + W", desc: "Open / Close Welcome Hub & Cheat Sheet", cat: "System" },
                { key: "SUPER + SHIFT + I", desc: "Launch Calamares Graphical Installer", cat: "System" },
                { key: "SUPER / SUPER + SPACE", desc: "Open Application Launcher", cat: "Desktop" },
                { key: "SUPER + RETURN", desc: "Open Kitty Terminal", cat: "Apps" },
                { key: "SUPER + E", desc: "Open Thunar File Manager", cat: "Apps" },
                { key: "SUPER + C", desc: "Close Active Window", cat: "Windows" },
                { key: "SUPER + V", desc: "Toggle Floating / Tiling Window", cat: "Windows" },
                { key: "SUPER + J / P", desc: "Toggle Split / Pseudo-Tile Layout", cat: "Windows" },
                { key: "SUPER + Arrows", desc: "Move Focus Between Windows", cat: "Windows" },
                { key: "SUPER + 1 – 0", desc: "Switch to Workspace 1 – 10", cat: "Workspaces" },
                { key: "SUPER + SHIFT + 1 – 0", desc: "Move Window to Workspace 1 – 10", cat: "Workspaces" },
                { key: "SUPER + S", desc: "Toggle Special Scratchpad Workspace", cat: "Workspaces" },
                { key: "SUPER + I", desc: "Toggle System Control Center", cat: "Panels" },
                { key: "SUPER + K", desc: "Toggle Quick Keybinds Popup", cat: "Panels" },
                { key: "SUPER + N", desc: "Toggle Notification Center", cat: "Panels" },
                { key: "SUPER + SHIFT + V", desc: "Toggle Clipboard History (cliphist)", cat: "Panels" },
                { key: "SUPER + M", desc: "Toggle Media & Audio Player", cat: "Panels" },
                { key: "SUPER + L", desc: "Toggle Calendar & Clock Dropdown", cat: "Panels" },
                { key: "SUPER + Q", desc: "Open Power Menu (Lock / Reboot / Off)", cat: "System" },
                { key: "SUPER + = / - / BS", desc: "Volume Up / Down / Mute Audio", cat: "Audio" }
            ];
            for (let i = 0; i < binds.length; i++) {
                cheatSheetModel.append(binds[i]);
            }
        }
    }

    // Click outside card to dismiss
    MouseArea {
        anchors.fill: parent
        onClicked: rootScope.closeAll()
    }

    Rectangle {
        width: 780
        height: 550
        anchors.centerIn: parent
        color: "#1a1b26"
        border.color: "#7aa2f7"
        border.width: 2
        radius: 14

        // Prevent clicks inside card from closing window
        MouseArea {
            anchors.fill: parent
            onClicked: {}
        }

        Shortcut {
            sequence: "Escape"
            enabled: welcomeWindow.visible
            onActivated: rootScope.closeAll()
        }

        Shortcut {
            sequence: "Tab"
            enabled: welcomeWindow.visible
            onActivated: welcomeWindow.activeTab = (welcomeWindow.activeTab === 0 ? 1 : 0)
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 14

            // Top Header Banner
            RowLayout {
                Layout.fillWidth: true
                spacing: 14

                Image {
                    Layout.preferredWidth: 42
                    Layout.preferredHeight: 42
                    sourceSize.width: 84; sourceSize.height: 84
                    source: Qt.resolvedUrl("cachyos_logo.png")
                    fillMode: Image.PreserveAspectFit
                }

                ColumnLayout {
                    spacing: 2
                    Text {
                        text: "Welcome to Jacob's Custom Arch Linux"
                        color: "#c0caf5"
                        font.family: "JetBrainsMono Nerd Font"
                        font.bold: true
                        font.pixelSize: 16
                    }
                    Text {
                        text: "Hyprland + Quickshell (TokyoNight) • Btrfs + Timeshift Rollback • UEFI & BIOS Ready"
                        color: "#7aa2f7"
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 11
                    }
                }

                Item { Layout.fillWidth: true }

                // Close Button
                Rectangle {
                    width: 30; height: 30; radius: 8
                    color: closeMouse.containsMouse ? "#f7768e" : "#24283b"
                    border.color: "#3b4261"
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "✕"
                        color: closeMouse.containsMouse ? "#1a1b26" : "#c0caf5"
                        font.family: "JetBrainsMono Nerd Font"
                        font.bold: true
                        font.pixelSize: 13
                    }

                    MouseArea {
                        id: closeMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: rootScope.closeAll()
                    }
                }
            }

            // Tab Switcher Row
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Rectangle {
                    Layout.fillWidth: true
                    height: 38
                    radius: 8
                    color: welcomeWindow.activeTab === 0 ? "#283457" : (tab0Mouse.containsMouse ? "#24283b" : "#16161e")
                    border.color: welcomeWindow.activeTab === 0 ? "#7aa2f7" : "#3b4261"
                    border.width: 1

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 8
                        Text {
                            text: "🚀  First-Boot Essential Apps"
                            color: welcomeWindow.activeTab === 0 ? "#c0caf5" : "#9aa5ce"
                            font.family: "JetBrainsMono Nerd Font"
                            font.bold: true
                            font.pixelSize: 12
                        }
                    }

                    MouseArea {
                        id: tab0Mouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: welcomeWindow.activeTab = 0
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 38
                    radius: 8
                    color: welcomeWindow.activeTab === 1 ? "#283457" : (tab1Mouse.containsMouse ? "#24283b" : "#16161e")
                    border.color: welcomeWindow.activeTab === 1 ? "#bb9af7" : "#3b4261"
                    border.width: 1

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 8
                        Text {
                            text: "⌨️  Keybindings Cheat Sheet"
                            color: welcomeWindow.activeTab === 1 ? "#c0caf5" : "#9aa5ce"
                            font.family: "JetBrainsMono Nerd Font"
                            font.bold: true
                            font.pixelSize: 12
                        }
                    }

                    MouseArea {
                        id: tab1Mouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: welcomeWindow.activeTab = 1
                    }
                }
            }

            // TAB 0: Essential First-Boot Apps Grid (2 Columns x 5 Rows)
            GridView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: welcomeWindow.activeTab === 0
                cellWidth: 365
                cellHeight: 68
                clip: true
                model: essentialAppsModel

                delegate: Item {
                    required property string title
                    required property string subtitle
                    required property string icon
                    required property string accent
                    required property string cmd
                    width: 365
                    height: 68

                    Rectangle {
                        anchors.fill: parent
                        anchors.rightMargin: 8
                        anchors.bottomMargin: 8
                        radius: 10
                        color: cardMouse.containsMouse ? "#283457" : "#24283b"
                        border.color: cardMouse.containsMouse ? accent : "#3b4261"
                        border.width: 1
                        Behavior on color { ColorAnimation { duration: 120 } }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 12

                            Rectangle {
                                Layout.preferredWidth: 40
                                Layout.preferredHeight: 40
                                radius: 8
                                color: "#1a1b26"
                                border.color: "#3b4261"
                                border.width: 1

                                Image {
                                    anchors.centerIn: parent
                                    width: 28; height: 28
                                    sourceSize.width: 64; sourceSize.height: 64
                                    source: icon
                                    fillMode: Image.PreserveAspectFit
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Text {
                                    text: title
                                    color: "#c0caf5"
                                    font.family: "JetBrainsMono Nerd Font"
                                    font.bold: true
                                    font.pixelSize: 12
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }

                                Text {
                                    text: subtitle
                                    color: "#9aa5ce"
                                    font.family: "JetBrainsMono Nerd Font"
                                    font.pixelSize: 10
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                            }

                            Rectangle {
                                Layout.preferredWidth: 58
                                Layout.preferredHeight: 26
                                radius: 6
                                color: cardMouse.containsMouse ? accent : "#1a1b26"
                                border.color: accent
                                border.width: 1

                                Text {
                                    anchors.centerIn: parent
                                    text: "Open"
                                    color: cardMouse.containsMouse ? "#1a1b26" : accent
                                    font.family: "JetBrainsMono Nerd Font"
                                    font.bold: true
                                    font.pixelSize: 10
                                }
                            }
                        }

                        MouseArea {
                            id: cardMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                rootScope.closeAll();
                                appRunner.exec(["sh", "-c", cmd]);
                            }
                        }
                    }
                }
            }

            // TAB 1: Keybindings Cheat Sheet (2-Column Grid)
            GridView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: welcomeWindow.activeTab === 1
                cellWidth: 365
                cellHeight: 42
                clip: true
                model: cheatSheetModel

                delegate: Item {
                    required property string key
                    required property string desc
                    required property string cat
                    width: 365
                    height: 42

                    Rectangle {
                        anchors.fill: parent
                        anchors.rightMargin: 8
                        anchors.bottomMargin: 6
                        radius: 8
                        color: "#24283b"
                        border.color: "#3b4261"
                        border.width: 1

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            spacing: 8

                            Rectangle {
                                Layout.preferredWidth: keyLabel.implicitWidth + 14
                                Layout.preferredHeight: 24
                                radius: 5
                                color: "#1a1b26"
                                border.color: "#7aa2f7"
                                border.width: 1

                                Text {
                                    id: keyLabel
                                    anchors.centerIn: parent
                                    text: key
                                    color: "#7aa2f7"
                                    font.family: "JetBrainsMono Nerd Font"
                                    font.bold: true
                                    font.pixelSize: 10
                                }
                            }

                            Text {
                                text: desc
                                color: "#c0caf5"
                                font.family: "JetBrainsMono Nerd Font"
                                font.pixelSize: 10
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }
                    }
                }
            }

            // Footer Bar
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#3b4261"
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                // Autostart Checkbox Button
                Rectangle {
                    width: 240
                    height: 30
                    radius: 6
                    color: autoMouse.containsMouse ? "#283457" : "#24283b"
                    border.color: welcomeWindow.autostartEnabled ? "#9ece6a" : "#3b4261"
                    border.width: 1

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 8

                        Text {
                            text: welcomeWindow.autostartEnabled ? "☑" : "☐"
                            color: welcomeWindow.autostartEnabled ? "#9ece6a" : "#565f89"
                            font.family: "JetBrainsMono Nerd Font"
                            font.pixelSize: 13
                        }

                        Text {
                            text: "Show Welcome on Startup"
                            color: "#c0caf5"
                            font.family: "JetBrainsMono Nerd Font"
                            font.pixelSize: 11
                        }
                    }

                    MouseArea {
                        id: autoMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            welcomeWindow.autostartEnabled = !welcomeWindow.autostartEnabled;
                            if (welcomeWindow.autostartEnabled) {
                                toggleAutostartProc.exec(["sh", "-c", "rm -f ~/.config/jacob-welcome-disabled"]);
                            } else {
                                toggleAutostartProc.exec(["sh", "-c", "touch ~/.config/jacob-welcome-disabled"]);
                            }
                        }
                    }
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: "Tip: Press SUPER + W anytime to reopen this hub • ESC to close"
                    color: "#565f89"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 10
                }
            }
        }
    }
}
