import QtQuick
import QtQuick.Layouts
import QtQuick.Templates
import qs.shared.theme
import qs.shared.controls

// Slider row (Caelestia Nexus SliderRow): leading icon, label plus current
// value on the first line, one delicate full-width slider below. The slim
// track and the thin handle that grows while pressed are the Nexus look;
// wheel input on the strip fine-tunes the value by `wheelStep` instead of
// scrolling the page.
ConnectedRect {
    id: root

    property string icon: ""
    property alias label: titleLabel.text
    property alias valueLabel: valueLabel.text
    property real value: 0
    property real from: 0
    property real to: 1
    property real stepSize: 0
    property real wheelStep: stepSize > 0 ? stepSize : (to - from) / 20

    signal moved(real value)

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
            color: Appearance.m3colors.m3onSurfaceVariant
        }

        ColumnLayout {
            id: column

            Layout.fillWidth: true
            spacing: Appearance.spacing.xSmall

            RowLayout {
                Layout.fillWidth: true
                spacing: Appearance.spacing.small

                StyledText {
                    id: titleLabel

                    Layout.fillWidth: true
                    color: Appearance.m3colors.m3onSurface
                    font.pixelSize: Typography.bodyMedium.pixelSize
                    elide: Text.ElideRight
                }

                StyledText {
                    id: valueLabel

                    color: Appearance.m3colors.m3outline
                    font.pixelSize: Typography.bodyMedium.pixelSize
                }
            }

            // Wheel strip wrapping the slider: wheel events the slider does
            // not accept bubble up here and adjust the value.
            MouseArea {
                id: wheelStrip

                Layout.fillWidth: true
                Layout.preferredHeight: Metrics.controlHeightS

                function onWheel(event: WheelEvent): void {
                    if (event.angleDelta.y > 0)
                        root.moved(Math.min(root.to, root.value + root.wheelStep));
                    else if (event.angleDelta.y < 0)
                        root.moved(Math.max(root.from, root.value - root.wheelStep));
                }

                // Unstyled Slider (QtQuick.Templates): behaviour only, all
                // visuals live in the contentItem below.
                Slider {
                    id: slider

                    // visualPosition tracks `value`; while dragging the
                    // Binding below overrides pos so the handle follows the
                    // finger before the consumer writes the value back.
                    property real pos: visualPosition

                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    implicitHeight: Metrics.spacingM

                    from: root.from
                    to: root.to
                    stepSize: root.stepSize
                    value: root.value
                    enabled: root.enabled

                    Binding {
                        target: slider
                        property: "pos"
                        value: Math.max(0, Math.min(1, dragArea.pressStartPos + dragArea.dragMovement))
                        when: dragArea.pressed
                    }

                    MouseArea {
                        id: dragArea

                        property real pressStartX
                        property real pressStartPos
                        property real dragMovement

                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        height: Metrics.controlHeightS
                        preventStealing: true

                        onPressed: event => {
                            dragArea.pressStartX = event.x;
                            dragArea.pressStartPos = slider.visualPosition;
                        }
                        onPositionChanged: event => {
                            dragArea.dragMovement = (event.x - dragArea.pressStartX) / width;
                            root.moved(slider.from + slider.pos * (slider.to - slider.from));
                        }
                        onReleased: event => {
                            if (dragArea.dragMovement === 0) {
                                const clickPos = Math.max(0, Math.min(1, event.x / width));
                                root.moved(slider.from + clickPos * (slider.to - slider.from));
                            } else {
                                root.moved(slider.from + slider.pos * (slider.to - slider.from));
                            }
                            dragArea.dragMovement = 0;
                        }
                    }

                    contentItem: Item {
                        // Remaining track past the handle; thins and fades
                        // as it collapses against the right edge dot.
                        Rectangle {
                            id: remaining

                            readonly property real fade: Math.min(width, 12) / 12

                            anchors.left: handle.right
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: Appearance.spacing.xSmall
                            height: slider.height * (slider.height <= 12 ? fade : Math.min(fade * 2, 1))
                            radius: Appearance.rounding.extraSmall / 2
                            topLeftRadius: Appearance.rounding.extraSmall / 2
                            bottomLeftRadius: Appearance.rounding.extraSmall / 2
                            color: slider.enabled ? Appearance.m3colors.m3secondaryContainer :
                                                    Appearance.applyAlpha(Appearance.m3colors.m3onSurface,
                                                                          0.1)
                        }

                        Rectangle {
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.rightMargin: 4 * remaining.fade
                            width: 4 * remaining.fade
                            height: width
                            radius: Appearance.rounding.full
                            color: filled.color
                        }

                        Rectangle {
                            id: filled

                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            width: (parent.width - handle.width - Appearance.spacing.xSmall) * slider.pos
                            height: slider.height
                            radius: Appearance.rounding.extraSmall / 2
                            topRightRadius: Appearance.rounding.extraSmall / 2
                            bottomRightRadius: Appearance.rounding.extraSmall / 2
                            color: slider.enabled ? Appearance.m3colors.m3primary : Appearance.applyAlpha(
                                                        Appearance.m3colors.m3onSurface, 0.38)

                            Behavior on width {
                                enabled: !dragArea.pressed
                                NumberAnimation {
                                    duration: Appearance.animation.expressiveFastEffects.duration
                                    easing.type: Appearance.animation.expressiveFastEffects.type
                                    easing.bezierCurve: Appearance.animation.expressiveFastEffects.bezierCurve
                                }
                            }
                        }

                        Rectangle {
                            id: handle

                            anchors.left: filled.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: Appearance.spacing.xSmall
                            width: 4
                            height: slider.height * (dragArea.pressed ? 1.6 : 1.25)
                            radius: Appearance.rounding.full
                            color: filled.color

                            Behavior on height {
                                NumberAnimation {
                                    duration: Appearance.animation.expressiveFastSpatial.duration
                                    easing.type: Appearance.animation.expressiveFastSpatial.type
                                    easing.bezierCurve: Appearance.animation.expressiveFastSpatial.bezierCurve
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
