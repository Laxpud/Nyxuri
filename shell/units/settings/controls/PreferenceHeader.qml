import QtQuick
import QtQuick.Layouts
import qs.shared.theme
import qs.shared.controls

// Section label above a connected card group (Caelestia Nexus SectionHeader).
// `first` removes the top margin for the leading section of a page; the
// top margin compensates the owning ColumnLayout's own spacing so the gap
// between groups stays one spacing unit.
StyledText {
    property bool first: false

    Layout.fillWidth: true
    Layout.topMargin: first ? 0 : Appearance.spacing.medium - ((parent as ColumnLayout).spacing ?? 0)
    Layout.bottomMargin: Appearance.spacing.xSmall
    Layout.leftMargin: Appearance.spacing.xSmall

    color: Appearance.m3colors.m3onSurfaceVariant
    font.pixelSize: Typography.labelMedium.pixelSize
    font.weight: Typography.labelMedium.weight
    elide: Text.ElideRight
}
