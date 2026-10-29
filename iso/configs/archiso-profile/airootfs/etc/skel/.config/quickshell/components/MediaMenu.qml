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
    margins { top: 40; right: 60 }
    
    WlrLayershell.layer: WlrLayer.Overlay
    exclusionMode: ExclusionMode.Ignore
    visible: rootScope.mediaOpen
    color: "transparent"

    implicitWidth: 320
    implicitHeight: 200

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
        border.color: "#3b4261"
        border.width: 1
        radius: 12

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "Media & Audio Controls"
                color: "#bb9af7"
                font.bold: true
                font.pixelSize: 14
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
                color: "#c0caf5"
                font.pixelSize: 12
            }

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 12

                Repeater {
                    model: [
                        { label: "⏮", cmd: "playerctl previous" },
                        { label: "⏯", cmd: "playerctl play-pause" },
                        { label: "⏭", cmd: "playerctl next" },
                        { label: "🔉", cmd: "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-" },
                        { label: "🔊", cmd: "wpctl set-volume -l 1.5 @DEFAULT_AUDIO_SINK@ 5%+" }
                    ]

                    delegate: Rectangle {
                        required property var modelData
                        width: 42; height: 34; radius: 6
                        color: mBtnMouse.containsMouse ? "#3b4261" : "#24283b"
                        border.color: "#3b4261"; border.width: 1
                        Text {
                            anchors.centerIn: parent
                            text: modelData.label
                            color: "#7aa2f7"
                            font.pixelSize: 13
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
