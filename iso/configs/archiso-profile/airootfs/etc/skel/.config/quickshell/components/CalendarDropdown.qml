import Quickshell
import Quickshell.Wayland
import Quickshell.Services.Notifications
import QtQuick
import QtQuick.Layouts

PanelWindow {
    required property var targetScreen
    required property var rootScope

    screen: targetScreen
    anchors { top: true; left: true }
    margins { top: 44; left: (targetScreen.width / 2) - (implicitWidth / 2) }

    WlrLayershell.layer: WlrLayer.Overlay
    exclusionMode: ExclusionMode.Ignore
    visible: rootScope.calendarOpen
    color: "transparent"

    implicitWidth: 360
    implicitHeight: 460

    property var now: new Date()
    property int currentYear: now.getFullYear()
    property int currentMonth: now.getMonth()
    property int firstDayOffset: new Date(currentYear, currentMonth, 1).getDay()
    property int daysInMonth: new Date(currentYear, currentMonth + 1, 0).getDate()

    Rectangle {
        anchors.fill: parent
        color: "#1a1b26"
        border.color: "#7aa2f7"
        border.width: 1
        radius: 12

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 8

                Text {
                    text: "󰃭"
                    color: "#7aa2f7"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 16
                }

                Text {
                    text: Qt.formatDateTime(now, "dddd, MMMM d, yyyy")
                    color: "#c0caf5"
                    font.family: "JetBrainsMono Nerd Font"
                    font.pixelSize: 13
                    font.bold: true
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: "#3b4261"
            }

            // Days of Week Header Row
            Row {
                Layout.alignment: Qt.AlignHCenter
                spacing: 8
                Repeater {
                    model: ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
                    Item {
                        width: 40; height: 20
                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            color: "#7aa2f7"
                            font.family: "JetBrainsMono Nerd Font"
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }
                }
            }

            // Dynamic Grid for Calendar Days
            Grid {
                Layout.alignment: Qt.AlignHCenter
                columns: 7
                rowSpacing: 6
                columnSpacing: 8

                Repeater {
                    model: 42
                    Rectangle {
                        required property int index
                        width: 40
                        height: 30
                        radius: 6

                        property int dayNum: index - firstDayOffset + 1
                        property bool isCurrentMonth: dayNum > 0 && dayNum <= daysInMonth
                        property bool isToday: isCurrentMonth && dayNum === now.getDate()

                        color: isToday ? "#7aa2f7" : (isCurrentMonth ? "#24283b" : "transparent")
                        border.color: isToday ? "#7aa2f7" : (isCurrentMonth ? "#3b4261" : "transparent")
                        border.width: isCurrentMonth ? 1 : 0

                        Text {
                            anchors.centerIn: parent
                            text: parent.isCurrentMonth ? parent.dayNum : ""
                            color: parent.isToday ? "#1a1b26" : "#c0caf5"
                            font.family: "JetBrainsMono Nerd Font"
                            font.pixelSize: 11
                            font.bold: parent.isToday
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
                text: "󰂚  Recent Notifications"
                color: "#bb9af7"
                font.family: "JetBrainsMono Nerd Font"
                font.pixelSize: 12
                font.bold: true
            }

            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 8
                model: NotificationServer.trackedNotifications

                delegate: Rectangle {
                    required property var modelData
                    width: ListView.view.width
                    height: 45
                    color: "#24283b"
                    border.color: "#3b4261"
                    border.width: 1
                    radius: 8

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        Text { text: modelData.summary; color: "#c0caf5"; font.family: "JetBrainsMono Nerd Font"; font.bold: true; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
                        Text { text: modelData.body; color: "#a9b1d6"; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 10; elide: Text.ElideRight; Layout.fillWidth: true }
                    }
                }
            }
        }
    }
}
