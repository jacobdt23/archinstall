import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import Quickshell.Services.SystemTray
import QtQuick
import QtQuick.Layouts

PanelWindow {
    required property var targetScreen
    required property var rootScope

    screen: targetScreen
    anchors { top: true; left: true; right: true }
    WlrLayershell.layer: WlrLayer.Top
    implicitHeight: 38
    exclusiveZone: 38
    color: "#1a1b26"

    property string cpuUsage: "0%"
    property string memUsage: "0%"
    property string diskUsage: "0%"

    Process { id: topBarExec }

    // Bottom subtle border line
    Rectangle {
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 1
        color: "#292e42"
    }

    Timer {
        interval: 2500
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            cpuProc.running = true;
            memProc.running = true;
            diskProc.running = true;
        }
    }

    Process {
        id: cpuProc
        command: ["sh", "-c", "awk '/^cpu / {u=$2+$4; t=$2+$4+$5; if(t>0) printf \"%d\", (u*100)/t}' /proc/stat"]
        stdout: SplitParser { onRead: data => { if (data.trim() !== "") cpuUsage = data.trim() + "%"; } }
    }

    Process {
        id: memProc
        command: ["sh", "-c", "free | awk '/^Mem:/ {print int($3/$2 * 100)}'"]
        stdout: SplitParser { onRead: data => { if (data.trim() !== "") memUsage = data.trim() + "%"; } }
    }

    Process {
        id: diskProc
        command: ["sh", "-c", "df / --output=pcent | tail -1 | tr -d ' %\\t'"]
        stdout: SplitParser { onRead: data => { if (data.trim() !== "") diskUsage = data.trim() + "%"; } }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        spacing: 8

        // App Menu Badge
        Rectangle {
            width: 28; height: 26; radius: 6
            color: logoTopMouse.containsMouse ? "#3b4261" : "#24283b"
            border.color: rootScope.launcherOpen ? "#7aa2f7" : "#3b4261"
            border.width: 1
            Behavior on color { ColorAnimation { duration: 150 } }

            Image {
                anchors.centerIn: parent
                width: 16; height: 16
                source: Qt.resolvedUrl("cachyos_logo.png")
                fillMode: Image.PreserveAspectFit
            }

            MouseArea {
                id: logoTopMouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    let s = rootScope.launcherOpen;
                    rootScope.closeAll();
                    rootScope.launcherOpen = !s;
                }
            }
        }

        // Workspaces Module
        RowLayout {
            spacing: 5
            Repeater {
                model: {
                    let screenIndex = Quickshell.screens.indexOf(targetScreen);
                    return screenIndex === 0 ? [1, 2, 3, 4, 5] : [6, 7, 8, 9, 10];
                }

                Rectangle {
                    required property var modelData
                    property bool isFocused: (Hyprland.focusedWorkspace && Hyprland.focusedWorkspace.id === modelData)
                    property bool isHovered: wsMouse.containsMouse

                    height: 26
                    width: isFocused ? 32 : 26
                    radius: 6
                    color: isFocused ? "#7aa2f7" : (isHovered ? "#3b4261" : "#24283b")
                    border.color: isFocused ? "#7aa2f7" : "#3b4261"
                    border.width: 1

                    Behavior on width { NumberAnimation { duration: 150 } }
                    Behavior on color { ColorAnimation { duration: 150 } }

                    Text {
                        anchors.centerIn: parent
                        text: modelData
                        color: parent.isFocused ? "#1a1b26" : "#c0caf5"
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 11
                        font.bold: true
                    }

                    MouseArea {
                        id: wsMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: topBarExec.exec(["hyprctl", "dispatch", "workspace", modelData.toString()])
                    }
                }
            }
        }

        Item { Layout.fillWidth: true }

        // Center Clock & Calendar Pill
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            height: 26
            implicitWidth: clockRow.implicitWidth + 20
            radius: 6
            color: clockArea.containsMouse ? "#3b4261" : "#24283b"
            border.color: rootScope.calendarOpen ? "#7aa2f7" : "#3b4261"
            border.width: 1
            z: 10

            Behavior on color { ColorAnimation { duration: 150 } }

            RowLayout {
                id: clockRow
                anchors.centerIn: parent
                spacing: 6

                Text {
                    text: "󰃭"
                    color: "#7aa2f7"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 13
                }

                Text {
                    id: clockText
                    color: "#c0caf5"
                    font.family: "JetBrainsMono Nerd Font"
                    font.bold: true
                    font.pixelSize: 11
                    text: Qt.formatDateTime(new Date(), "MMM d • hh:mm AP")
                    Timer {
                        interval: 1000; running: true; repeat: true
                        onTriggered: parent.text = Qt.formatDateTime(new Date(), "MMM d • hh:mm AP")
                    }
                }
            }

            MouseArea {
                id: clockArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    let w = rootScope.calendarOpen;
                    rootScope.closeAll();
                    rootScope.calendarOpen = !w;
                }
            }
        }

        Item { Layout.fillWidth: true }

        // System Tray Items
        RowLayout {
            spacing: 6

            Repeater {
                model: SystemTray.items

                delegate: Rectangle {
                    required property var modelData
                    visible: modelData.icon !== ""
                    width: 26; height: 26; radius: 6
                    color: trayMouse.containsMouse ? "#3b4261" : "#24283b"
                    border.color: "#3b4261"; border.width: 1

                    Behavior on color { ColorAnimation { duration: 150 } }

                    Image {
                        id: trayImg
                        anchors.centerIn: parent
                        width: 16; height: 16
                        source: modelData.icon
                        fillMode: Image.PreserveAspectFit
                        visible: status === Image.Ready
                    }

                    Text {
                        anchors.centerIn: parent
                        visible: trayImg.status !== Image.Ready
                        text: "󰀂"
                        color: "#7aa2f7"
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 13
                    }

                    MouseArea {
                        id: trayMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: mouse => {
                            if (mouse.button === Qt.RightButton) {
                                modelData.display(parent, mouse.x, mouse.y);
                            } else {
                                modelData.activate();
                            }
                        }
                    }
                }
            }
        }

        // System Resource Pills (CPU, MEM, DISK)
        RowLayout {
            spacing: 6

            Rectangle {
                height: 26; implicitWidth: cpuText.implicitWidth + 16; radius: 6
                color: cpuArea.containsMouse ? "#3b4261" : "#24283b"
                border.color: "#3b4261"; border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }
                Text {
                    id: cpuText
                    anchors.centerIn: parent
                    text: "󰻠 " + cpuUsage
                    color: "#7aa2f7"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 11
                    font.bold: true
                }
                MouseArea { id: cpuArea; anchors.fill: parent; hoverEnabled: true; onClicked: topBarExec.exec(["sh", "-c", "kitty -e btop || alacritty -e btop"]) }
            }

            Rectangle {
                height: 26; implicitWidth: memText.implicitWidth + 16; radius: 6
                color: memArea.containsMouse ? "#3b4261" : "#24283b"
                border.color: "#3b4261"; border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }
                Text {
                    id: memText
                    anchors.centerIn: parent
                    text: "󰍛 " + memUsage
                    color: "#bb9af7"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 11
                    font.bold: true
                }
                MouseArea { id: memArea; anchors.fill: parent; hoverEnabled: true; onClicked: topBarExec.exec(["sh", "-c", "kitty -e btop || alacritty -e btop"]) }
            }

            Rectangle {
                height: 26; implicitWidth: diskText.implicitWidth + 16; radius: 6
                color: diskArea.containsMouse ? "#3b4261" : "#24283b"
                border.color: "#3b4261"; border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }
                Text {
                    id: diskText
                    anchors.centerIn: parent
                    text: "󰋊 " + diskUsage
                    color: "#e0af68"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 11
                    font.bold: true
                }
                MouseArea { id: diskArea; anchors.fill: parent; hoverEnabled: true; onClicked: topBarExec.exec(["sh", "-c", "kitty -e ncdu || alacritty -e ncdu"]) }
            }
        }

        // Media / Audio Quick Toggle
        Rectangle {
            width: 26; height: 26; radius: 6
            color: mediaMouse.containsMouse ? "#3b4261" : "#24283b"
            border.color: rootScope.mediaOpen ? "#9ece6a" : "#3b4261"; border.width: 1
            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "󰕾"
                color: "#9ece6a"
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: 14
            }

            MouseArea {
                id: mediaMouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    let m = rootScope.mediaOpen;
                    rootScope.closeAll();
                    rootScope.mediaOpen = !m;
                }
            }
        }

        // Notification Toggle Button
        Rectangle {
            width: 26; height: 26; radius: 6
            color: notifMouse.containsMouse ? "#3b4261" : "#24283b"
            border.color: rootScope.notificationsOpen ? "#7aa2f7" : "#3b4261"; border.width: 1
            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "󰂚"
                color: "#7aa2f7"
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: 13
            }

            MouseArea {
                id: notifMouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    let n = rootScope.notificationsOpen;
                    rootScope.closeAll();
                    rootScope.notificationsOpen = !n;
                }
            }
        }

        // Power Menu Button
        Rectangle {
            width: 26; height: 26; radius: 6
            color: powerMouse.containsMouse ? "#f7768e" : "#24283b"
            border.color: "#f7768e"; border.width: 1
            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "󰐥"
                color: powerMouse.containsMouse ? "#1a1b26" : "#f7768e"
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: 13
            }

            MouseArea {
                id: powerMouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    let p = rootScope.powerMenuOpen;
                    rootScope.closeAll();
                    rootScope.powerMenuOpen = !p;
                }
            }
        }
    }
}
