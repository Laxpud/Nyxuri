import QtQuick
import QtQuick.Layouts
import qs.shared.theme
import qs.shared.controls

// Action/navigation row (Caelestia Nexus RowButton + NavRow): leading icon,
// double-line text, trailing chevron by default. Used both for entering
// subpages and for firing one-shot actions; the sublabel animates its text
// changes so live values (e.g. the current device name) roll instead of
// hard-cutting.
ConnectedRect {
    id: root

    property alias icon: iconLabel.text
    property alias text: titleLabel.text
    property alias subtext: subLabel.text
    property string trailingIcon: "chevron_right"

    signal clicked

    Layout.fillWidth: true
    implicitHeight: column.implicitHeight + Appearance.spacing.medium * 2
    opacity: enabled ? 1 : 0.5

    Behavior on opacity {
        NumberAnimation {
            duration: Appearance.animation.expressiveFastEffects.duration
            easing.type: Appearance.animation.expressiveFastEffects.type
            easing.bezierCurve: Appearance.animation.expressiveFastEffects.bezierCurve
        }
    }

    StateLayer {
        id: stateLayer

        anchors.fill: parent
        layerRadius: (root.first || root.last) ? Appearance.rounding.extraLarge :
                                                 Appearance.rounding.extraSmall

        color: Appearance.m3colors.m3onSurface
        hovered: rowPress.containsMouse
        pressed: rowPress.pressed
    }

    MouseArea {
        id: rowPress

        anchors.fill: parent
        enabled: root.enabled
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }

    RowLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Appearance.spacing.panelPadding
        anchors.rightMargin: Appearance.spacing.panelPadding
        spacing: Appearance.spacing.small

        MaterialSymbol {
            id: iconLabel

            visible: text.length > 0
            Layout.preferredWidth: text.length > 0 ? implicitWidth : 0
            iconSize: Metrics.iconM
            fill: 1
            color: Appearance.m3colors.m3onSurfaceVariant
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
                id: subLabel

                Layout.fillWidth: true
                visible: text.length > 0
                color: Appearance.m3colors.m3outline
                font.pixelSize: Typography.labelSmall.pixelSize
                elide: Text.ElideRight
                animateChange: true
            }
        }

        MaterialSymbol {
            visible: root.trailingIcon.length > 0
            Layout.preferredWidth: root.trailingIcon.length > 0 ? implicitWidth : 0
            text: root.trailingIcon
            iconSize: Metrics.iconM
            color: Appearance.m3colors.m3onSurfaceVariant
        }
    }
}
