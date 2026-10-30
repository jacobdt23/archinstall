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
    margins { top: 44; right: 48 }

    WlrLayershell.layer: WlrLayer.Overlay
    exclusionMode: ExclusionMode.Ignore
    visible: rootScope.mediaOpen
    color: "transparent"

    implicitWidth: 330
    implicitHeight: 195

    property string trackInfo: "No active media session"
    Process { id: mediaActionProc }

    Process {
        id: mediaStatusProc
        command: ["sh", "-c", "playerctl metadata --format '{{artist}} - {{title}}' 2>/dev/null || echo 'No active media session'"]
        stdout: SplitParser {
            onRead: data => {
                let t = data.trim();
                if (t !== "" && t !== " - ") trackInfo = t;
                else trackInfo = "No active media session";
            }
        }
    }

    Timer {
        interval: 2000
        running: rootScope.mediaOpen
        repeat: true
        triggeredOnStart: true
        onTriggered: mediaStatusProc.running = true
    }

    Rectangle {
        anchors.fill: parent
        color: "#1a1b26"
        border.color: "#9ece6a"
        border.width: 1
        radius: 12

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Text {
                    text: "󰕾"
                    color: "#9ece6a"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 16
                }

                Text {
                    text: "Media & Audio Controls"
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

            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: trackInfo
                elide: Text.ElideRight
                color: "#a9b1d6"
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: 11
            }

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 10

                Repeater {
                    model: [
                        { label: "󰒮", cmd: "playerctl previous" },
                        { label: "󰐎", cmd: "playerctl play-pause" },
                        { label: "󰒭", cmd: "playerctl next" },
                        { label: "󰕿", cmd: "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-" },
                        { label: "󰕾", cmd: "wpctl set-volume -l 1.5 @DEFAULT_AUDIO_SINK@ 5%+" },
                        { label: "󰝟", cmd: "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle" }
                    ]

                    delegate: Rectangle {
                        required property var modelData
                        width: 40; height: 34; radius: 8
                        color: mBtnMouse.containsMouse ? "#3b4261" : "#24283b"
                        border.color: mBtnMouse.containsMouse ? "#9ece6a" : "#3b4261"
                        border.width: 1
                        Text {
                            anchors.centerIn: parent
                            text: modelData.label
                            color: "#9ece6a"
                            font.family: "JetBrainsMono Nerd Font"
                            font.pixelSize: 15
                        }
                        MouseArea {
                            id: mBtnMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: {
                                mediaActionProc.exec(["sh", "-c", modelData.cmd]);
                                mediaStatusProc.running = true;
                            }
                        }
                    }
                }
            }
        }
    }
}
