import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import QtQuick.Layouts

PanelWindow {
    required property var targetScreen
    required property var rootScope

    screen: targetScreen
    anchors { top: true; right: true }
    margins { top: 44; right: 14 }

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
    color: "transparent"
    visible: rootScope.controlCenterOpen

    implicitWidth: 340
    implicitHeight: 390

    Process { id: ccProc }

    Rectangle {
        anchors.fill: parent
        color: "#1a1b26"
        border.color: "#bb9af7"
        border.width: 1
        radius: 12

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Image {
                    Layout.preferredWidth: 20
                    Layout.preferredHeight: 20
                    sourceSize.width: 40; sourceSize.height: 40
                    source: Qt.resolvedUrl("cachyos_logo.png")
                    fillMode: Image.PreserveAspectFit
                }

                Text {
                    text: "System Control Center"
                    color: "#c0caf5"
                    font.family: "JetBrainsMono Nerd Font"
                    font.bold: true
                    font.pixelSize: 13
                }

                Item { Layout.fillWidth: true }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#3b4261"
            }

            Repeater {
                model: [
                    { icon: "file:///usr/share/icons/hicolor/scalable/apps/calamares.svg", color: "#9ece6a", label: "Install System (Calamares)", cmd: "/usr/local/bin/launch-calamares" },
                    { icon: "file:///usr/share/icons/hicolor/scalable/apps/org.pulseaudio.pavucontrol.svg", color: "#7aa2f7", label: "Audio Mixer (Pavucontrol)", cmd: "pavucontrol" },
                    { icon: "file:///usr/share/icons/hicolor/256x256/apps/blueman.png", color: "#7dcfff", label: "Bluetooth Manager (Blueman)", cmd: "blueman-manager" },
                    { icon: "file:///usr/share/icons/hicolor/scalable/apps/nm-device-wired.svg", color: "#e0af68", label: "Network Manager (nmtui)", cmd: "kitty -e nmtui || alacritty -e nmtui" },
                    { icon: "file:///usr/share/icons/hicolor/scalable/apps/btop.svg", color: "#bb9af7", label: "System Monitor (btop)", cmd: "kitty -e btop || alacritty -e btop" },
                    { icon: "file:///usr/share/icons/hicolor/256x256/apps/kitty.png", color: "#7aa2f7", label: "Reload Hyprland Config", cmd: "hyprctl reload && notify-send 'Hyprland' 'Config Reloaded'" },
                    { icon: "file:///usr/share/pixmaps/archlinux-logo.svg", color: "#f7768e", label: "Lock Screen (Hyprlock)", cmd: "hyprlock" }
                ]

                delegate: Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    height: 38
                    color: ccItemMouse.containsMouse ? "#3b4261" : "#24283b"
                    border.color: ccItemMouse.containsMouse ? modelData.color : "#3b4261"
                    border.width: 1
                    radius: 8

                    Behavior on color { ColorAnimation { duration: 120 } }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 10

                        Image {
                            Layout.preferredWidth: 22
                            Layout.preferredHeight: 22
                            sourceSize.width: 48; sourceSize.height: 48
                            source: modelData.icon
                            fillMode: Image.PreserveAspectFit
                        }

                        Text {
                            text: modelData.label
                            color: "#c0caf5"
                            font.family: "JetBrainsMono Nerd Font"
                            font.pixelSize: 11
                            font.bold: true
                            Layout.fillWidth: true
                        }
                    }

                    MouseArea {
                        id: ccItemMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            rootScope.closeAll();
                            ccProc.exec(["sh", "-c", modelData.cmd]);
                        }
                    }
                }
            }
        }
    }
}
