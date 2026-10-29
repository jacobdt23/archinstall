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
    margins { top: 40; right: 100 }
    
    WlrLayershell.layer: WlrLayer.Overlay
    exclusionMode: ExclusionMode.Ignore
    visible: rootScope.clipboardOpen
    color: "transparent"

    implicitWidth: 340
    implicitHeight: 380

    ListModel { id: clipModel }
    Process { id: copyProc }

    Process {
        id: listProc
        command: ["sh", "-c", "cliphist list 2>/dev/null | head -n 25"]
        stdout: SplitParser {
            onRead: data => {
                let line = data.trim();
                if (line !== "") {
                    let display = line.replace(/^[0-9]+\t/, "");
                    clipModel.append({ rawEntry: line, previewText: display });
                }
            }
        }
    }

    onVisibleChanged: {
        if (visible) {
            clipModel.clear();
            listProc.running = true;
        }
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

            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: "Clipboard History"
                    color: "#7aa2f7"
                    font.bold: true
                    font.pixelSize: 14
                }
                Item { Layout.fillWidth: true }
                Rectangle {
                    width: 56; height: 22; radius: 4
                    color: clearMouse.containsMouse ? "#f7768e" : "#24283b"
                    border.color: "#3b4261"; border.width: 1
                    Text {
                        anchors.centerIn: parent
                        text: "Clear"
                        color: clearMouse.containsMouse ? "#1a1b26" : "#c0caf5"
                        font.pixelSize: 10; font.bold: true
                    }
                    MouseArea {
                        id: clearMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            copyProc.exec(["cliphist", "wipe"]);
                            clipModel.clear();
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#3b4261"
            }

            Text {
                visible: clipModel.count === 0
                Layout.alignment: Qt.AlignHCenter
                text: "Clipboard is empty"
                color: "#565f89"
                font.pixelSize: 12
            }

            ListView {
                visible: clipModel.count > 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 6
                model: clipModel

                delegate: Rectangle {
                    required property string rawEntry
                    required property string previewText
                    width: ListView.view.width
                    height: 38
                    color: clipItemMouse.containsMouse ? "#3b4261" : "#24283b"
                    border.color: "#3b4261"
                    border.width: 1
                    radius: 6

                    Text {
                        anchors.fill: parent
                        anchors.margins: 10
                        verticalAlignment: Text.AlignVCenter
                        text: previewText
                        elide: Text.ElideRight
                        color: "#c0caf5"
                        font.pixelSize: 11
                    }

                    MouseArea {
                        id: clipItemMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            let id = rawEntry.split("\t")[0];
                            copyProc.exec(["sh", "-c", "cliphist decode " + id + " | wl-copy"]);
                            rootScope.closeAll();
                        }
                    }
                }
            }
        }
    }
}
