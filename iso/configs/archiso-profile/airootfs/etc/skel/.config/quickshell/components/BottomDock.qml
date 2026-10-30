import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import QtQuick.Layouts

PanelWindow {
    required property var targetScreen
    required property var rootScope

    screen: targetScreen
    anchors { bottom: true; left: true; right: true }
    WlrLayershell.layer: WlrLayer.Top
    implicitHeight: 40
    exclusiveZone: 40
    color: "#1a1b26"

    Process { id: dockExec }

    property bool hasCalamares: false
    Process {
        id: checkCalamaresProc
        command: ["sh", "-c", "test -x /usr/local/bin/launch-calamares && echo yes || echo no"]
        running: true
        stdout: SplitParser {
            onRead: data => {
                if (data.trim() === "yes") hasCalamares = true
            }
        }
    }

    RowLayout {
        anchors.centerIn: parent
        spacing: 12

        // App Launcher Button with bundled logo
        Rectangle {
            width: 32; height: 32; radius: 6
            color: btn1Mouse.containsMouse ? "#3b4261" : "#24283b"
            border.color: "#3b4261"
            border.width: 1
            Behavior on color { ColorAnimation { duration: 150 } }

            Image {
                anchors.centerIn: parent
                width: 20; height: 20
                source: Qt.resolvedUrl("cachyos_logo.png")
                fillMode: Image.PreserveAspectFit
            }

            MouseArea {
                id: btn1Mouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    let s = rootScope.launcherOpen
                    rootScope.closeAll()
                    rootScope.launcherOpen = !s
                }
            }
        }

        // Terminal Shortcut
        Rectangle {
            width: 32; height: 32; radius: 6
            color: btn2Mouse.containsMouse ? "#3b4261" : "#24283b"
            border.color: "#3b4261"
            border.width: 1
            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: ">_"
                color: "#9ece6a"
                font.pixelSize: 12
                font.bold: true
            }

            MouseArea {
                id: btn2Mouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: dockExec.exec(["sh", "-c", "command -v kitty >/dev/null && exec kitty || exec alacritty"])
            }
        }

        // File Manager Shortcut
        Rectangle {
            width: 32; height: 32; radius: 6
            color: btnFilesMouse.containsMouse ? "#3b4261" : "#24283b"
            border.color: "#3b4261"
            border.width: 1
            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "F"
                color: "#7aa2f7"
                font.pixelSize: 13
                font.bold: true
            }

            MouseArea {
                id: btnFilesMouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: dockExec.exec(["thunar"])
            }
        }

        // Browser Shortcut
        Rectangle {
            width: 32; height: 32; radius: 6
            color: btn3Mouse.containsMouse ? "#3b4261" : "#24283b"
            border.color: "#3b4261"
            border.width: 1
            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "W"
                color: "#ff9e64"
                font.pixelSize: 14
                font.bold: true
            }

            MouseArea {
                id: btn3Mouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: dockExec.exec(["sh", "-c", "for b in brave firefox chromium; do command -v $b >/dev/null && exec $b; done; xdg-open https://archlinux.org"])
            }
        }

        // Control Center Shortcut
        Rectangle {
            width: 32; height: 32; radius: 6
            color: btnCcMouse.containsMouse ? "#3b4261" : "#24283b"
            border.color: "#3b4261"
            border.width: 1
            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "⚙"
                color: "#bb9af7"
                font.pixelSize: 14
                font.bold: true
            }

            MouseArea {
                id: btnCcMouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    let s = rootScope.controlCenterOpen
                    rootScope.closeAll()
                    rootScope.controlCenterOpen = !s
                }
            }
        }

        // Calamares Installer Pill (visible only in Live ISO environment)
        Rectangle {
            visible: hasCalamares
            width: 82; height: 32; radius: 6
            color: btnInstallMouse.containsMouse ? "#9ece6a" : "#7aa2f7"
            border.color: "#bb9af7"
            border.width: 1
            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: "⬇ Install"
                color: "#1a1b26"
                font.pixelSize: 12
                font.bold: true
            }

            MouseArea {
                id: btnInstallMouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: dockExec.exec(["/usr/local/bin/launch-calamares"])
            }
        }
    }
}
