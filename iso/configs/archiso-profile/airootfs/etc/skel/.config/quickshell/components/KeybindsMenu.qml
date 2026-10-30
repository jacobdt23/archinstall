import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import QtQuick.Layouts

PanelWindow {
    required property var targetScreen
    required property var rootScope

    screen: targetScreen
    anchors { top: true; left: true }
    margins { top: 44; left: 16 }

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
    exclusionMode: ExclusionMode.Ignore
    visible: rootScope.keybindsOpen
    color: "transparent"

    implicitWidth: 460
    implicitHeight: 500

    ListModel {
        id: keybindMasterModel

        Component.onCompleted: {
            let binds = [
                { key: "SUPER + SHIFT + I", desc: "Install System (Calamares)" },
                { key: "SUPER + RETURN", desc: "Open Terminal (Kitty)" },
                { key: "SUPER / SUPER + SPACE", desc: "Toggle Application Launcher" },
                { key: "SUPER + E", desc: "Open File Manager (Thunar)" },
                { key: "SUPER + C", desc: "Close Focused Window" },
                { key: "SUPER + I", desc: "Toggle Control Center" },
                { key: "SUPER + K", desc: "Toggle Keybinds Reference" },
                { key: "SUPER + N", desc: "Toggle Notifications Center" },
                { key: "SUPER + SHIFT + V", desc: "Toggle Clipboard History" },
                { key: "SUPER + M", desc: "Toggle Media Controls" },
                { key: "SUPER + L", desc: "Toggle Calendar & Agenda" },
                { key: "SUPER + Q", desc: "Toggle Power Menu" },
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

    ListModel { id: filteredKeybinds }

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
        border.color: "#e0af68"
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
                    text: "󰌌"
                    color: "#e0af68"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 16
                }

                Text {
                    text: "Keybindings Reference"
                    color: "#c0caf5"
                    font.family: "JetBrainsMono Nerd Font"
                    font.bold: true
                    font.pixelSize: 13
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 36
                color: "#24283b"
                border.color: "#3b4261"
                border.width: 1
                radius: 8

                TextInput {
                    id: kbSearchInput
                    anchors.fill: parent
                    anchors.margins: 8
                    color: "#c0caf5"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 11
                    focus: true
                    verticalAlignment: TextInput.AlignVCenter
                    onTextChanged: filterKeybinds(text)
                }

                Text {
                    anchors.fill: parent
                    anchors.margins: 8
                    verticalAlignment: Text.AlignVCenter
                    text: "󰍉  Search keybinds..."
                    color: "#565f89"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 11
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
                    required property string key
                    required property string desc
                    width: ListView.view.width
                    height: 36
                    color: "#24283b"
                    border.color: "#3b4261"
                    border.width: 1
                    radius: 8

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        Text { text: key; color: "#7aa2f7"; font.family: "JetBrainsMono Nerd Font"; font.bold: true; font.pixelSize: 11 }
                        Item { Layout.fillWidth: true }
                        Text { text: desc; color: "#c0caf5"; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 11 }
                    }
                }
            }
        }
    }
}
