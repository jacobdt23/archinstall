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
    implicitHeight: 54
    exclusiveZone: 54
    color: "transparent"

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

    // Floating Rounded TokyoNight Dock Container
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 6
        height: 46
        width: dockRow.implicitWidth + 24
        radius: 12
        color: "#1a1b26"
        border.color: "#3b4261"
        border.width: 1

        RowLayout {
            id: dockRow
            anchors.centerIn: parent
            spacing: 10

            // 1. App Launcher Button with Custom Arch Logo
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnLauncherMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: rootScope.launcherOpen ? "#7aa2f7" : "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Image {
                    anchors.centerIn: parent
                    width: 22; height: 22
                    source: Qt.resolvedUrl("cachyos_logo.png")
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    id: btnLauncherMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        let s = rootScope.launcherOpen
                        rootScope.closeAll()
                        rootScope.launcherOpen = !s
                    }
                }
            }

            // 2. Terminal (Official Kitty Icon)
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnTermMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Image {
                    anchors.centerIn: parent
                    width: 24; height: 24
                    sourceSize.width: 64; sourceSize.height: 64
                    source: "file:///usr/share/icons/hicolor/256x256/apps/kitty.png"
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    id: btnTermMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: dockExec.exec(["sh", "-c", "command -v kitty >/dev/null && exec kitty || exec alacritty"])
                }
            }

            // 3. File Manager (Official Thunar Icon)
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnFilesMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Image {
                    anchors.centerIn: parent
                    width: 24; height: 24
                    sourceSize.width: 64; sourceSize.height: 64
                    source: "file:///usr/share/icons/hicolor/128x128/apps/org.xfce.thunar.png"
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    id: btnFilesMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: dockExec.exec(["thunar"])
                }
            }

            // 4. Web Browser (Official Firefox Icon)
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnBrowserMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Image {
                    anchors.centerIn: parent
                    width: 24; height: 24
                    sourceSize.width: 64; sourceSize.height: 64
                    source: "file:///usr/share/icons/hicolor/256x256/apps/firefox.png"
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    id: btnBrowserMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: dockExec.exec(["sh", "-c", "for b in brave firefox chromium; do command -v $b >/dev/null && exec $b; done; xdg-open https://archlinux.org"])
                }
            }

            // 5. OBS Studio (Official OBS Icon)
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnObsMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Image {
                    anchors.centerIn: parent
                    width: 24; height: 24
                    sourceSize.width: 64; sourceSize.height: 64
                    source: "file:///usr/share/icons/hicolor/256x256/apps/com.obsproject.Studio.png"
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    id: btnObsMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: dockExec.exec(["obs"])
                }
            }

            // 6. VLC Media Player (Official VLC Icon)
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnVlcMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Image {
                    anchors.centerIn: parent
                    width: 24; height: 24
                    sourceSize.width: 64; sourceSize.height: 64
                    source: "file:///usr/share/icons/hicolor/256x256/apps/vlc.png"
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    id: btnVlcMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: dockExec.exec(["vlc"])
                }
            }

            // 7. Timeshift Btrfs Snapshots (Official Timeshift Icon)
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnTsMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Image {
                    anchors.centerIn: parent
                    width: 24; height: 24
                    sourceSize.width: 64; sourceSize.height: 64
                    source: "file:///usr/share/icons/hicolor/128x128/apps/timeshift.png"
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    id: btnTsMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: dockExec.exec(["/usr/local/bin/timeshift-launcher"])
                }
            }

            // 7. System Control Center (Official Volume/Settings Icon)
            Rectangle {
                width: 34; height: 34; radius: 8
                color: btnCcMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: rootScope.controlCenterOpen ? "#bb9af7" : "#3b4261"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                Image {
                    anchors.centerIn: parent
                    width: 22; height: 22
                    sourceSize.width: 48; sourceSize.height: 48
                    source: "file:///usr/share/icons/hicolor/scalable/apps/btop.svg"
                    fillMode: Image.PreserveAspectFit
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

            // Separator before Calamares Installer Pill
            Rectangle {
                visible: hasCalamares
                width: 1; height: 24
                color: "#3b4261"
            }

            // 8. Calamares Installer Pill (Official Calamares Icon)
            Rectangle {
                visible: hasCalamares
                width: installRow.implicitWidth + 22
                height: 34
                radius: 8
                color: btnInstallMouse.containsMouse ? "#3b4261" : "#24283b"
                border.color: "#7aa2f7"
                border.width: 1
                Behavior on color { ColorAnimation { duration: 150 } }

                RowLayout {
                    id: installRow
                    anchors.centerIn: parent
                    spacing: 8

                    Image {
                        Layout.preferredWidth: 22
                        Layout.preferredHeight: 22
                        sourceSize.width: 48; sourceSize.height: 48
                        source: "file:///usr/share/icons/hicolor/scalable/apps/calamares.svg"
                        fillMode: Image.PreserveAspectFit
                    }

                    Text {
                        text: "Install Arch"
                        color: "#7aa2f7"
                        font.family: "JetBrainsMono Nerd Font"
                        font.pixelSize: 11
                        font.bold: true
                    }
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
}
