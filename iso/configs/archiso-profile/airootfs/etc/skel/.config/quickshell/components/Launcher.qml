import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import QtQuick.Layouts

PanelWindow {
    required property var targetScreen
    required property var rootScope

    screen: targetScreen
    anchors { top: true; left: true; right: true; bottom: true }

    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    color: "#660f0f17"
    visible: rootScope.launcherOpen

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: rootScope.launcherOpen = false
    }

    ListModel { id: appModel }
    ListModel { id: filteredModel }

    Process { id: launchProc }

    Process {
        id: appProc
        command: ["/usr/local/bin/list-desktop-apps"]
        running: true
        stdout: SplitParser {
            onRead: data => {
                let line = data.trim();
                if (line !== "") {
                    let parts = line.split("\t");
                    let entry = {
                        appName: parts[0] || "",
                        appDesc: parts[1] || "Application",
                        desktopId: parts[2] || "",
                        appIcon: parts[3] ? ("file://" + parts[3]) : ""
                    };
                    appModel.append(entry);
                    filteredModel.append(entry);
                }
            }
        }
    }

    function filterApps(query) {
        filteredModel.clear();
        let q = query.toLowerCase();
        for (let i = 0; i < appModel.count; i++) {
            let item = appModel.get(i);
            if (item.appName.toLowerCase().includes(q) || item.appDesc.toLowerCase().includes(q)) {
                filteredModel.append({
                    appName: item.appName,
                    appDesc: item.appDesc,
                    desktopId: item.desktopId,
                    appIcon: item.appIcon
                });
            }
        }
    }

    function launchEntry(desktopId, appName) {
        rootScope.launcherOpen = false;
        if (desktopId === "calamares") {
            launchProc.exec(["/usr/local/bin/launch-calamares"]);
        } else {
            launchProc.exec(["sh", "-c", "setsid gtk-launch \"" + desktopId + "\" >/dev/null 2>&1 &"]);
        }
    }

    onVisibleChanged: {
        if (visible) {
            searchInput.text = "";
            searchInput.forceActiveFocus();
        }
    }

    Rectangle {
        anchors.centerIn: parent
        width: 540
        height: 480
        color: "#1a1b26"
        border.color: "#7aa2f7"
        border.width: 1
        radius: 14

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: {}
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 18
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Image {
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    sourceSize.width: 44
                    sourceSize.height: 44
                    source: Qt.resolvedUrl("cachyos_logo.png")
                    fillMode: Image.PreserveAspectFit
                }

                Text {
                    text: "Application Launcher"
                    color: "#c0caf5"
                    font.family: "JetBrainsMono Nerd Font"
                    font.bold: true
                    font.pixelSize: 14
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: "ESC to close"
                    color: "#565f89"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 10
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 38
                color: "#24283b"
                border.color: searchInput.activeFocus ? "#7aa2f7" : "#3b4261"
                border.width: 1
                radius: 8

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 8

                    Text {
                        text: "󰍉"
                        color: "#7aa2f7"
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 15
                    }

                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        TextInput {
                            id: searchInput
                            anchors.fill: parent
                            color: "#c0caf5"
                            font.family: "JetBrainsMono Nerd Font"
                            font.pixelSize: 12
                            focus: true
                            verticalAlignment: TextInput.AlignVCenter
                            onTextChanged: filterApps(text)
                            Keys.onEscapePressed: rootScope.launcherOpen = false
                            Keys.onReturnPressed: {
                                if (filteredModel.count > 0) {
                                    let first = filteredModel.get(0);
                                    launchEntry(first.desktopId, first.appName);
                                }
                            }
                        }

                        Text {
                            anchors.fill: parent
                            verticalAlignment: Text.AlignVCenter
                            text: "Search applications..."
                            color: "#565f89"
                            font.family: "JetBrainsMono Nerd Font"
                            font.pixelSize: 12
                            visible: searchInput.text.length === 0
                        }
                    }
                }
            }

            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 6
                model: filteredModel

                delegate: Rectangle {
                    required property string appName
                    required property string appDesc
                    required property string desktopId
                    required property string appIcon

                    width: ListView.view.width
                    height: 50
                    color: launcherMouse.containsMouse ? "#3b4261" : "#24283b"
                    border.color: launcherMouse.containsMouse ? "#7aa2f7" : "#3b4261"
                    border.width: 1
                    radius: 8

                    Behavior on color { ColorAnimation { duration: 120 } }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 12

                        Rectangle {
                            width: 34; height: 34; radius: 8
                            color: "#1a1b26"
                            border.color: "#3b4261"; border.width: 1

                            Image {
                                id: appIconImg
                                anchors.centerIn: parent
                                width: 24; height: 24
                                sourceSize.width: 48
                                sourceSize.height: 48
                                source: appIcon
                                fillMode: Image.PreserveAspectFit
                                asynchronous: true
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Text {
                                text: appName
                                color: "#c0caf5"
                                font.family: "JetBrainsMono Nerd Font"
                                font.bold: true
                                font.pixelSize: 12
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }

                            Text {
                                text: appDesc
                                color: "#565f89"
                                font.family: "JetBrainsMono Nerd Font"
                                font.pixelSize: 10
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }

                        Text {
                            text: "󰁔"
                            color: launcherMouse.containsMouse ? "#7aa2f7" : "#565f89"
                            font.family: "JetBrainsMono Nerd Font"
                            font.pixelSize: 14
                        }
                    }

                    MouseArea {
                        id: launcherMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: launchEntry(desktopId, appName)
                    }
                }
            }
        }
    }
}
