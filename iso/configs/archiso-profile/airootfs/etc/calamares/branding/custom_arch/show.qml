import QtQuick 2.0;
import calamares.slideshow 1.0;

Presentation
{
    id: presentation

    function nextSlide() {
        presentation.goToNextSlide();
    }

    Timer {
        id: advanceTimer
        interval: 4000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: nextSlide()
    }

    Slide {
        Image {
            id: logoImg
            source: "logo.png"
            width: 120; height: 120
            fillMode: Image.PreserveAspectFit
            anchors.centerIn: parent
        }
        Text {
            anchors.horizontalCenter: logoImg.horizontalCenter
            anchors.top: logoImg.bottom
            anchors.topMargin: 16
            text: "<b>Jacob's Custom Arch Linux</b><br/>" +
                  "Installing Hyprland + Quickshell (TokyoNight) Desktop..."
            wrapMode: Text.WordWrap
            width: presentation.width
            horizontalAlignment: Text.Center
        }
    }

    Slide {
        centeredText: qsTr("Configured for UEFI/GPT, BIOS/MBR, Bare Metal (NVIDIA, AMD, Intel) & Virtual Machines.")
    }

    function onActivate() {
        presentation.currentSlide = 0;
    }

    function onLeave() {
    }
}
