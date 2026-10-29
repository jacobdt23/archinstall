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
    margins { top: 40; right: 20 }

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    color: "#01000000"
    visible: rootScope.controlCenterOpen

    implicitWidth: 320
    implicitHeight: 340

    Process { id: ccProc }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: rootScope.controlCenterOpen = false
    }

    Rectangle {
        anchors.fill: parent
        color: "#1a1b26"
        border.color: "#3b4261"
        border.width: 1
        radius: 12

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: {}
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 10

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "System Control Center"
                color: "#7aa2f7"
                font.bold: true
                font.pixelSize: 14
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#3b4261"
            }

            Repeater {
                model: [
                    { label: "Audio Mixer (Pavucontrol)", cmd: "pavucontrol" },
                    { label: "Bluetooth Manager (Blueman)", cmd: "blueman-manager" },
                    { label: "Network Manager TUI", cmd: "kitty -e nmtui || alacritty -e nmtui" },
                    { label: "System Monitor (btop)", cmd: "kitty -e btop || alacritty -e btop" },
                    { label: "Reload Hyprland Config", cmd: "hyprctl reload && notify-send 'Hyprland' 'Config Reloaded'" },
                    { label: "Lock Screen (Hyprlock)", cmd: "hyprlock" }
                ]

                delegate: Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    height: 36
                    color: ccItemMouse.containsMouse ? "#3b4261" : "#24283b"
                    border.color: "#3b4261"
                    border.width: 1
                    radius: 6

                    Behavior on color { ColorAnimation { duration: 150 } }

                    Text {
                        anchors.centerIn: parent
                        text: modelData.label
                        color: "#c0caf5"
                        font.pixelSize: 12
                        font.bold: true
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
