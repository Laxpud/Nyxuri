import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import qs.shared.theme
import qs.shared.controls
import qs.shared.i18n

// Pill search bar (Caelestia Nexus SearchBar): one fully rounded capsule
// with a leading search glyph and a trailing clear button that fades in
// while there is text. The border breathes to the primary colour on focus.
// Root is the TextField: consumers bind text/activeFocus and handle
// textEdited/accepted directly.
TextField {
    id: root

    implicitHeight: Math.max(Metrics.controlHeightL, contentHeight + topPadding * 2)
    leftPadding: searchIcon.width + searchIcon.anchors.leftMargin + Appearance.spacing.small
    rightPadding: clearButton.width + clearButton.anchors.rightMargin + Appearance.spacing.small
    topPadding: Appearance.spacing.small
    bottomPadding: Appearance.spacing.small

    color: Appearance.m3colors.m3onSurface
    selectionColor: Appearance.applyAlpha(Appearance.m3colors.m3primary, 0.4)
    selectedTextColor: color
    placeholderTextColor: Appearance.m3colors.m3onSurfaceVariant
    verticalAlignment: TextInput.AlignVCenter
    selectByMouse: true
    font.family: Fonts.ui
    font.pixelSize: Typography.bodyLarge.pixelSize

    background: Rectangle {
        radius: Appearance.rounding.full
        color: Appearance.m3colors.m3surfaceContainerLowest
        border.width: root.activeFocus ? 2 : 1
        border.color: root.activeFocus ? Appearance.m3colors.m3primary : Appearance.m3colors.m3outlineVariant

        // The breathing focus border.
        Behavior on border.color {
            ColorAnimation {
                duration: Appearance.animation.expressiveDefaultEffects.duration
                easing.type: Appearance.animation.expressiveDefaultEffects.type
                easing.bezierCurve: Appearance.animation.expressiveDefaultEffects.bezierCurve
            }
        }

        Behavior on border.width {
            NumberAnimation {
                duration: Appearance.animation.expressiveDefaultEffects.duration
                easing.type: Appearance.animation.expressiveDefaultEffects.type
                easing.bezierCurve: Appearance.animation.expressiveDefaultEffects.bezierCurve
            }
        }
    }

    MaterialSymbol {
        id: searchIcon

        z: 1
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Appearance.spacing.medium
        text: "search"
        iconSize: Metrics.iconM
        color: Appearance.m3colors.m3onSurfaceVariant
    }

    IconButton {
        id: clearButton

        z: 1
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.rightMargin: Appearance.spacing.xSmall
        width: Metrics.controlHeightM
        height: Metrics.controlHeightM
        controlSize: Metrics.controlHeightM
        iconSize: Metrics.iconS + 2
        iconName: "close"
        accessibleName: I18n.tr("Clear")
        showTooltip: false
        enabled: root.text.length > 0
        opacity: enabled ? 1 : 0

        Behavior on opacity {
            NumberAnimation {
                duration: Appearance.animation.expressiveFastEffects.duration
                easing.type: Appearance.animation.expressiveFastEffects.type
                easing.bezierCurve: Appearance.animation.expressiveFastEffects.bezierCurve
            }
        }

        onClicked: {
            root.clear();
            root.forceActiveFocus();
        }
    }
}
