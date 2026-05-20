import QtQuick
import Caelestia.Config
import qs.components
import qs.services

Item {
    id: root

    required property DrawerVisibilities visibilities

    implicitWidth: Tokens.sizes.bar.innerWidth
    implicitHeight: layout.implicitHeight

    Column {
        id: layout

        anchors.centerIn: parent
        spacing: Tokens.spacing.small

        AnimatedImage {
            id: cat

            anchors.horizontalCenter: parent.horizontalCenter

            width: Tokens.sizes.bar.innerWidth + Tokens.padding.large * 3
            height: width
            source: Qt.resolvedUrl("../../../assets/final-cat.gif")
            asynchronous: true
            playing: true
            cache: false
            fillMode: AnimatedImage.PreserveAspectFit
        }

        Item {
            id: button

            anchors.horizontalCenter: parent.horizontalCenter
            implicitWidth: icon.implicitHeight + Tokens.padding.small * 1
            implicitHeight: icon.implicitHeight + Tokens.padding.small * 1

            StateLayer {
                anchors.fill: parent
                radius: Tokens.rounding.full
                onClicked: root.visibilities.session = !root.visibilities.session
            }

            MaterialIcon {
                id: icon

                anchors.centerIn: parent
                anchors.horizontalCenterOffset: -1

                text: "power_settings_new"
                color: Colours.palette.m3error
                font.bold: true
                font.pointSize: Tokens.font.size.normal
            }
        }
    }
}
