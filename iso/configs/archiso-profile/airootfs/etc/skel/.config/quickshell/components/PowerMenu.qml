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
    visible: rootScope.powerMenuOpen

    implicitWidth: 230
    implicitHeight: 215

    Process { id: powerProc }

    Rectangle {
        anchors.fill: parent
        color: "#1a1b26"
        border.color: "#f7768e"
        border.width: 1
        radius: 12

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Text {
                    text: "󰐥"
                    color: "#f7768e"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 15
                }

                Text {
                    text: "Session & Power"
                    color: "#c0caf5"
                    font.family: "JetBrainsMono Nerd Font"
                    font.bold: true
                    font.pixelSize: 13
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#3b4261"
            }

            Repeater {
                model: [
                    { icon: "󰌾", color: "#7aa2f7", label: "Lock Screen", cmd: "hyprlock" },
                    { icon: "󰜉", color: "#e0af68", label: "Reboot System", cmd: "systemctl reboot" },
                    { icon: "󰐥", color: "#f7768e", label: "Power Off", cmd: "systemctl poweroff" }
                ]

                delegate: Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    height: 38
                    color: pMouse.containsMouse ? "#3b4261" : "#24283b"
                    border.color: pMouse.containsMouse ? modelData.color : "#3b4261"
                    border.width: 1
                    radius: 8

                    Behavior on color { ColorAnimation { duration: 120 } }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 10

                        Text {
                            text: modelData.icon
                            color: modelData.color
                            font.family: "JetBrainsMono Nerd Font"
                            font.pixelSize: 15
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
                        id: pMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: {
                            rootScope.closeAll();
                            powerProc.exec(["sh", "-c", modelData.cmd]);
                        }
                    }
                }
            }
        }
    }
}
