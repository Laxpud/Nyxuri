import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import qs.shared.theme
import qs.shared.controls
import qs.shared.i18n

// Text input row (Caelestia Nexus TextFieldRow): double-line label on the
// left, one compact rounded field on the right. The field border "breathes"
// to the primary colour on focus, validation failures flip it to the error
// colour and swap the subtext for `errorText`, and a clear button appears
// while the field holds text. Unflushed edits are flushed through
// editingFinished on destruction so closing a page never drops input.
ConnectedRect {
    id: root

    property alias label: titleLabel.text
    property string subtext: ""
    property string value: ""
    property alias placeholderText: input.placeholderText
    property string errorText: ""
    property alias maximumLength: input.maximumLength
    property var validate
    property bool emptyIsValid: true
    property bool smallField: false
    property real fieldWidth: 250 * Metrics.scale
    property real smallFieldWidth: 100 * Metrics.scale
    readonly property alias field: input
    readonly property bool valid: !validate || (!input.text && emptyIsValid) || (validate instanceof RegExp
                                                                                 ? validate.test(input.text) :
                                                                                   !!validate(input.text))

    property bool isError: false

    signal valueEdited(string value)
    signal editingFinished(string value)

    function clear(): void {
        input.clear();
    }

    Layout.fillWidth: true
    implicitHeight: column.implicitHeight + Appearance.spacing.medium * 2

    Component.onDestruction: {
        if (value !== input.text)
            editingFinished(input.text);
    }

    RowLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: Appearance.spacing.panelPadding
        anchors.rightMargin: Appearance.spacing.panelPadding
        spacing: Appearance.spacing.small

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
                visible: root.subtext.length > 0 || (root.isError && root.errorText.length > 0)
                text: root.isError && root.errorText.length > 0 ? root.errorText : root.subtext
                color: root.isError && root.errorText.length > 0 ? Appearance.m3colors.m3error :
                                                                   Appearance.m3colors.m3outline
                font.pixelSize: Typography.labelSmall.pixelSize
                elide: Text.ElideRight
            }
        }

        TextField {
            id: input

            Layout.preferredWidth: root.smallField ? root.smallFieldWidth : root.fieldWidth
            Layout.maximumWidth: root.width / 2
            Layout.alignment: Qt.AlignVCenter
            implicitHeight: Metrics.controlHeightL

            text: root.value
            color: Appearance.m3colors.m3onSurface
            selectionColor: Appearance.applyAlpha(Appearance.m3colors.m3primary, 0.4)
            selectedTextColor: color
            placeholderTextColor: Appearance.m3colors.m3onSurfaceVariant
            verticalAlignment: TextInput.AlignVCenter
            selectByMouse: true
            font.family: Fonts.ui
            font.pixelSize: Typography.bodyMedium.pixelSize
            leftPadding: Appearance.spacing.small
            rightPadding: Appearance.spacing.small + (clearButton.visible ? clearButton.width : 0)

            onTextEdited: {
                if (root.isError)
                    root.isError = false;
                root.valueEdited(text);
            }
            onEditingFinished: {
                if (!root.valid)
                    root.isError = true;
                root.editingFinished(text);
            }

            background: Rectangle {
                radius: Appearance.rounding.small
                color: Appearance.m3colors.m3surfaceContainerHigh
                border.width: input.activeFocus ? 2 : 1
                border.color: root.isError ? Appearance.m3colors.m3error : input.activeFocus
                                             ? Appearance.m3colors.m3primary :
                                               Appearance.m3colors.m3outlineVariant

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

            IconButton {
                id: clearButton

                z: 1
                anchors.right: parent.right
                anchors.rightMargin: Appearance.spacing.xSmall
                anchors.verticalCenter: parent.verticalCenter
                width: Metrics.controlHeightM
                height: Metrics.controlHeightM
                controlSize: Metrics.controlHeightM
                iconSize: Metrics.iconS + 2
                iconName: "close"
                accessibleName: I18n.tr("Clear")
                showTooltip: false
                visible: input.text.length > 0 && input.enabled
                opacity: visible ? 1 : 0

                Behavior on opacity {
                    NumberAnimation {
                        duration: Appearance.animation.expressiveFastEffects.duration
                        easing.type: Appearance.animation.expressiveFastEffects.type
                        easing.bezierCurve: Appearance.animation.expressiveFastEffects.bezierCurve
                    }
                }

                onClicked: {
                    input.clear();
                    input.forceActiveFocus();
                }
            }
        }
    }
}
