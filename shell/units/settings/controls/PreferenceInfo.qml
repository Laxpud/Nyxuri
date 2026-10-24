import QtQuick
import QtQuick.Layouts
import qs.shared.theme
import qs.shared.controls

// Read-only property row (Caelestia Nexus InfoRow): leading icon, property
// name (plus optional subtext), and the value right-aligned in the variant
// colour. Pure display — no interaction, no state layer.
ConnectedRect {
    id: root

    property alias label: titleLabel.text
    property string subtext: ""
    property alias value: valueLabel.text
    property string icon: ""
    property color iconColor: Appearance.m3colors.m3onSurfaceVariant

    Layout.fillWidth: true
    implicitHeight: column.implicitHeight + Appearance.spacing.medium * 2

    RowLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Appearance.spacing.panelPadding
        anchors.rightMargin: Appearance.spacing.panelPadding
        spacing: Appearance.spacing.small

        MaterialSymbol {
            visible: root.icon.length > 0
            Layout.preferredWidth: root.icon.length > 0 ? implicitWidth : 0
            text: root.icon
            iconSize: Metrics.iconM
            fill: 1
            color: root.iconColor
        }

        ColumnLayout {
            id: column

            Layout.fillWidth: true
            spacing: 0

            StyledText {
                id: titleLabel

                Layout.fillWidth: true
                color: Appearance.m3colors.m3onSurface
                font.pixelSize: Typography.bodyMedium.pixelSize
                elide: Text.ElideRight
            }

            StyledText {
                Layout.fillWidth: true
                visible: root.subtext.length > 0
                text: root.subtext
                color: Appearance.m3colors.m3outline
                font.pixelSize: Typography.labelSmall.pixelSize
                elide: Text.ElideRight
            }
        }

        StyledText {
            id: valueLabel

            Layout.maximumWidth: root.width / 2
            horizontalAlignment: Text.AlignRight
            color: Appearance.m3colors.m3onSurfaceVariant
            font.pixelSize: Typography.bodyMedium.pixelSize
            elide: Text.ElideRight
        }
    }
}
