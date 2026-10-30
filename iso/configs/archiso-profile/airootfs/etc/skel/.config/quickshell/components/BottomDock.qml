import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import QtQuick.Layouts

PanelWindow {
    required property var targetScreen
    required property var rootScope

    screen: targetScreen
    anchors { bottom: true; left: true; right: true }
    WlrLayershell.layer: WlrLayer.Top
    implicitHeight: 54
    exclusiveZone: 54
    color: "transparent"

    Process { id: dockExec }

    property bool hasCalamares: false
    Process {
        id: checkCalamaresProc
        command: ["sh", "-c", "test -x /usr/local/bin/launch-calamares && echo yes || echo no"]
        running: true
        stdout: SplitParser {
            onRead: data => {
                if (data.trim() === "yes") hasCalamares = true
            }
        }
    }

    // Floating Rounded TokyoNight Dock Container
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 6
        height: 46
        width: dockRow.implicitWidth + 24
        radius: 12
        color: "#1a1b26"
        border.color: "#3b4261"
        border.width: 1

        RowLayout {
            id: dockRow
            anchors.centerIn: parent
            spacing: 10

            // 1. App Launcher Button with Custom Arch Logo
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnLauncherMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: rootScope.launcherOpen ? "#7aa2f7" : "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Image {
                    anchors.centerIn: parent
                    width: 20; height: 20
                    source: Qt.resolvedUrl("cachyos_logo.png")
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    id: btnLauncherMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        let s = rootScope.launcherOpen
                        rootScope.closeAll()
                        rootScope.launcherOpen = !s
                    }
                }
            }

            // 2. Terminal (Kitty)
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnTermMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: "󰆍"
                    color: "#9ece6a"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 18
                }

                MouseArea {
                    id: btnTermMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: dockExec.exec(["sh", "-c", "command -v kitty >/dev/null && exec kitty || exec alacritty"])
                }
            }

            // 3. File Manager (Thunar)
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnFilesMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: "󰉋"
                    color: "#7aa2f7"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 17
                }

                MouseArea {
                    id: btnFilesMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: dockExec.exec(["thunar"])
                }
            }

            // 4. Web Browser (Firefox)
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnBrowserMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: "󰈹"
                    color: "#ff9e64"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 18
                }

                MouseArea {
                    id: btnBrowserMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: dockExec.exec(["sh", "-c", "for b in brave firefox chromium; do command -v $b >/dev/null && exec $b; done; xdg-open https://archlinux.org"])
                }
            }

            // 5. Clipboard History
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnClipMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: rootScope.clipboardOpen ? "#7dcfff" : "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: "󰅌"
                    color: "#7dcfff"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 16
                }

                MouseArea {
                    id: btnClipMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        let c = rootScope.clipboardOpen
                        rootScope.closeAll()
                        rootScope.clipboardOpen = !c
                    }
                }
            }

            // 6. Keybindings Cheat Sheet
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnKbMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: rootScope.keybindsOpen ? "#e0af68" : "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: "󰌌"
                    color: "#e0af68"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 17
                }

                MouseArea {
                    id: btnKbMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        let k = rootScope.keybindsOpen
                        rootScope.closeAll()
                        rootScope.keybindsOpen = !k
                    }
                }
            }

            // 7. System Control Center
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnCcMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: rootScope.controlCenterOpen ? "#bb9af7" : "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: "󰒓"
                    color: "#bb9af7"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 17
                }

                MouseArea {
                    id: btnCcMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        let s = rootScope.controlCenterOpen
                        rootScope.closeAll()
                        rootScope.controlCenterOpen = !s
                    }
                }
            }

            // Separator before Calamares Installer Pill
            Rectangle {
                visible: hasCalamares
                width: 1; height: 24
                color: "#3b4261"
            }

            // 8. Calamares Installer Pill (visible only in Live ISO environment)
            Rectangle {
                visible: hasCalamares
                width: installRow.implicitWidth + 22
                height: 34
                radius: 8
                color: btnInstallMouse.containsMouse ? "#9ece6a" : "#7aa2f7"
                border.color: "#bb9af7"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                RowLayout {
                    id: installRow
                    anchors.centerIn: parent
                    spacing: 6

                    Text {
                        text: "󰇚"
                        color: "#1a1b26"
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 15
                    }

                    Text {
                        text: "Install Arch"
                        color: "#1a1b26"
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 11
                        font.bold: true
                    }
                }

                MouseArea {
                    id: btnInstallMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: dockExec.exec(["/usr/local/bin/launch-calamares"])
                }
            }
        }
    }
}
