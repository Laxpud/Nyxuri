import QtQuick
import qs.shared.theme

// Connected group base (Caelestia Nexus ConnectedRect). The first row of a
// group rounds only its top corners, the last row only its bottom corners,
// middle rows stay flat — stacked rows read as one connected MD3 card.
Rectangle {
    property bool first: false
    property bool last: false

    color: Appearance.m3colors.m3surfaceContainer
    topLeftRadius: first ? Appearance.rounding.extraLarge : Appearance.rounding.extraSmall
    topRightRadius: first ? Appearance.rounding.extraLarge : Appearance.rounding.extraSmall
    bottomLeftRadius: last ? Appearance.rounding.extraLarge : Appearance.rounding.extraSmall
    bottomRightRadius: last ? Appearance.rounding.extraLarge : Appearance.rounding.extraSmall
}
