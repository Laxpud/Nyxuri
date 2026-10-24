import QtQuick
import QtQuick.Layouts
import qs.shared.theme
import qs.shared.controls
import qs.units.settings

// Dropdown select row (Caelestia Nexus SelectRow): label plus optional
// subtext on the left, the current value shown in a tonal pill button on
// the right. Pressing the pill opens the shared MD3 menu; the page injects
// `inputRegionService` so menus that overhang the floating window keep
// compositor input.
ConnectedRect {
    id: root

    property alias label: titleLabel.text
    property string subtext: ""
    property alias model: splitButton.model
    property alias currentValue: splitButton.currentValue
    property var inputRegionService: null

    signal selected(string value)

    Layout.fillWidth: true
    implicitHeight: column.implicitHeight + NexusStyle.padding.medium * 2
    clip: false
    z: 0

    RowLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: NexusStyle.padding.largeIncreased
        anchors.rightMargin: NexusStyle.padding.largeIncreased
        spacing: NexusStyle.padding.small

        ColumnLayout {
            id: column

            Layout.fillWidth: true
            spacing: 0

            StyledText {
                id: titleLabel

                Layout.fillWidth: true
                color: Appearance.m3colors.m3onSurface
                font.pixelSize: NexusStyle.font.bodyMedium
                elide: Text.ElideRight
            }

            StyledText {
                Layout.fillWidth: true
                visible: root.subtext.length > 0
                text: root.subtext
                color: Appearance.m3colors.m3outline
                font.pixelSize: NexusStyle.font.labelSmall
                elide: Text.ElideRight
            }
        }

        SplitMenuButton {
            id: splitButton

            inputRegionService: root.inputRegionService
            onValueSelected: value => root.selected(value)
        }
    }
}
