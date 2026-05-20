import QtQuick
import Caelestia.Config
import qs.services

Item {
    id: root

    implicitWidth: Math.round(Tokens.font.size.large * 1.6)
    implicitHeight: Math.round(Tokens.font.size.large * 1.2)

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            const visibilities = Visibilities.getForActive();
            visibilities.launcher = !visibilities.launcher;
        }
    }

    AnimatedImage {
        anchors.centerIn: parent
        width: parent.implicitWidth
        height: parent.implicitHeight
        source: Qt.resolvedUrl("../../../assets/cat-scratches.gif")
        asynchronous: true
        playing: true
        cache: false
        fillMode: AnimatedImage.PreserveAspectFit
    }
}
