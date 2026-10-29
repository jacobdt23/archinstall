import Quickshell
import Quickshell.Wayland
import QtQuick
import QtQuick.Layouts

PanelWindow {
    required property var screen
    required property var rootScope

    screen: screen
    anchors { top: true; left: true }
    margins { top: 40; left: 20 }
    
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
    exclusionMode: ExclusionMode.Ignore
    visible: rootScope.keybindsOpen
    color: "transparent"

    implicitWidth: 440
    implicitHeight: 480

    ListModel {
        id: keybindMasterModel

        Component.onCompleted: {
            let binds = [
                { key: "SUPER + RETURN", desc: "Open Terminal (Kitty)" },
                { key: "SUPER + C", desc: "Close Focused Window" },
                { key: "SUPER + Q", desc: "Toggle Power Menu" },
                { key: "SUPER + E", desc: "Open File Manager (Thunar)" },
                { key: "SUPER + D", desc: "Open Discord" },
                { key: "SUPER + W", desc: "Launch Looking Glass Client" },
                { key: "SUPER / SUPER + SPACE", desc: "Toggle Application Launcher" },
                { key: "SUPER + I", desc: "Toggle Control Center" },
                { key: "SUPER + K", desc: "Toggle Keybinds Reference" },
                { key: "SUPER + N", desc: "Toggle Notifications Center" },
                { key: "SUPER + SHIFT + V", desc: "Toggle Clipboard History" },
                { key: "SUPER + M", desc: "Toggle Media Controls" },
                { key: "SUPER + L", desc: "Toggle Calendar & Agenda" },
                { key: "SUPER + V", desc: "Toggle Floating Mode" },
                { key: "SUPER + P", desc: "Pseudo Tile Layout" },
                { key: "SUPER + J", desc: "Toggle Split Layout" },
                { key: "SUPER + = / - / BS", desc: "Volume Up / Down / Mute" },
                { key: "SUPER + 1-0", desc: "Switch to Workspaces 1-10" },
                { key: "SUPER + SHIFT + 1-0", desc: "Move Window to Workspace 1-10" },
                { key: "SUPER + S", desc: "Toggle Special Scratchpad" }
            ];
            for (let i = 0; i < binds.length; i++) {
                keybindMasterModel.append(binds[i]);
                filteredKeybinds.append(binds[i]);
            }
        }
    }

    ListModel {
        id: filteredKeybinds
    }

    function filterKeybinds(query) {
        filteredKeybinds.clear();
        for (let i = 0; i < keybindMasterModel.count; i++) {
            let item = keybindMasterModel.get(i);
            let q = query.toLowerCase();
            if (item.key.toLowerCase().includes(q) || item.desc.toLowerCase().includes(q)) {
                filteredKeybinds.append(item);
            }
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

            Text {
                text: "Keybindings Reference"
                color: "#bb9af7"
                font.bold: true
                font.pixelSize: 14
            }

            Rectangle {
                Layout.fillWidth: true
                height: 35
                color: "#24283b"
                border.color: "#3b4261"
                border.width: 1
                radius: 6

                TextInput {
                    id: kbSearchInput
                    anchors.fill: parent
                    anchors.margins: 8
                    color: "#c0caf5"
                    focus: true
                    verticalAlignment: TextInput.AlignVCenter
                    onTextChanged: filterKeybinds(text)
                }

                Text {
                    anchors.fill: parent
                    anchors.margins: 8
                    verticalAlignment: Text.AlignVCenter
                    text: "Search keybinds..."
                    color: "#565f89"
                    visible: kbSearchInput.text.length === 0
                }
            }

            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 6
                model: filteredKeybinds

                delegate: Rectangle {
                    width: ListView.view.width
                    height: 35
                    color: "#24283b"
                    border.color: "#3b4261"
                    border.width: 1
                    radius: 6

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        Text { text: key; color: "#7aa2f7"; font.bold: true; font.pixelSize: 11 }
                        Item { Layout.fillWidth: true }
                        Text { text: desc; color: "#c0caf5"; font.pixelSize: 11 }
                    }
                }
            }
        }
    }
}
