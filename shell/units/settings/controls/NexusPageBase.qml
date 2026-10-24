import QtQuick
import QtQuick.Layouts
import qs.shared.theme
import qs.shared.controls
import qs.shared.i18n

// Detail page scaffold (Caelestia Nexus PageBase): big title, optional
// subpage back arrow, one scrolling column of content capped at
// `maxContentWidth`. Pages declare a single content child (the default
// property) — typically a ColumnLayout anchored to cappedWidth. The back
// arrow emits backRequested; navigation state stays with the host (T3 M2).
ColumnLayout {
    id: root

    required property string title
    property bool isSubPage: false
    property real maxContentWidth: 800 * Metrics.scale
    readonly property int cappedWidth: Math.min(maxContentWidth, width)
    readonly property alias flickable: flick

    default property Item contentChild

    signal backRequested

    spacing: Metrics.spacingXL

    // Block clicks from reaching the flickable's top margin so the title
    // area settles focus out of text fields instead of scrolling.
    MouseArea {
        z: 1
        implicitWidth: header.implicitWidth
        implicitHeight: header.implicitHeight - Layout.bottomMargin
        Layout.bottomMargin: -flick.topMargin

        onClicked: root.forceActiveFocus()

        RowLayout {
            id: header

            spacing: Appearance.spacing.medium

            IconButton {
                visible: root.isSubPage
                Layout.preferredWidth: root.isSubPage ? implicitWidth : 0
                variant: "tonal"
                iconName: "arrow_back"
                iconSize: Metrics.iconM
                accessibleName: I18n.tr("Go back")
                showTooltip: false
                onClicked: root.backRequested()
            }

            StyledText {
                Layout.fillWidth: true
                text: root.title
                color: Appearance.m3colors.m3onSurface
                font.pixelSize: Typography.titleLarge.pixelSize
                elide: Text.ElideRight
            }
        }
    }

    StyledFlickable {
        id: flick

        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.topMargin: -topMargin
        topMargin: Appearance.spacing.medium
        bottomMargin: Appearance.spacing.large

        contentHeight: root.contentChild ? root.contentChild.implicitHeight : 0
        contentItem.children: root.contentChild ? [root.contentChild] : []

        TapHandler {
            onTapped: root.forceActiveFocus()
        }
    }
}
