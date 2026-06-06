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

        Item {
            id: catHitbox

            anchors.horizontalCenter: parent.horizontalCenter

            readonly property var catGifs: [
                "cat-scratches.gif",
                "dance-cat.gif",
                "final-cat.gif"
            ]

            property int gifIndex: 2

            width: cat.width
            height: cat.height

            StateLayer {
                anchors.fill: parent
                onClicked: {
                    catHitbox.gifIndex = (catHitbox.gifIndex + 1) % catHitbox.catGifs.length;
                    cat.source = Qt.resolvedUrl("../../../assets/" + catHitbox.catGifs[catHitbox.gifIndex]);
                    cat.playing = true;
                }
            }

            AnimatedImage {
                id: cat

                anchors.centerIn: parent

                width: Tokens.sizes.bar.innerWidth + Tokens.padding.large * 3
                height: width
                source: Qt.resolvedUrl("../../../assets/" + catHitbox.catGifs[catHitbox.gifIndex])
                asynchronous: true
                playing: true
                cache: false
                fillMode: AnimatedImage.PreserveAspectFit
            }
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
