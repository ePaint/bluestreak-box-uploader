"""Reusable card widget with rounded corners and shadow effect."""

import qtawesome as qta
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QGraphicsDropShadowEffect,
    QPushButton,
)
from PySide6.QtGui import QColor, QIcon

from gui.theme import COLORS, SPACING, SIZES


class Card(QFrame):
    """Modern card container with rounded corners and optional header."""

    collapsed_changed = Signal(bool)  # Emitted when collapse state changes

    def __init__(
        self,
        title: str = "",
        icon: QIcon | None = None,
        parent: QWidget | None = None,
        hover_effect: bool = False,
        collapsible: bool = False,
        collapsed: bool = False,
    ):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._hover_effect = hover_effect
        self._collapsible = collapsible
        self._collapsed = collapsed
        self._setup_ui()
        self._apply_style()
        if collapsible and collapsed:
            self._content_widget.setVisible(False)

    def _setup_ui(self) -> None:
        """Set up the card layout."""
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(
            SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"]
        )
        self._main_layout.setSpacing(SPACING["sm"])

        # Header (if title provided)
        if self._title:
            self._header = QWidget()
            header_layout = QHBoxLayout(self._header)
            header_layout.setContentsMargins(0, 0, 0, SPACING["xs"])
            header_layout.setSpacing(SPACING["sm"])

            # Icon (if provided)
            if self._icon:
                self._icon_label = QLabel()
                self._icon_label.setPixmap(self._icon.pixmap(SIZES["icon_sm"], SIZES["icon_sm"]))
                self._icon_label.setFixedSize(SIZES["icon_md"], SIZES["icon_md"])
                self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                header_layout.addWidget(self._icon_label)

            # Title
            self._title_label = QLabel(self._title)
            self._title_label.setObjectName("cardTitle")
            header_layout.addWidget(self._title_label)

            # Badge placeholder (right side)
            self._badge_label = QLabel()
            self._badge_label.setObjectName("cardBadge")
            self._badge_label.hide()
            header_layout.addStretch()
            header_layout.addWidget(self._badge_label)

            # Collapse button (if collapsible)
            if self._collapsible:
                self._collapse_btn = QPushButton()
                self._collapse_btn.setObjectName("collapseBtn")
                self._collapse_btn.setFixedSize(SIZES["collapse_btn"], SIZES["collapse_btn"])
                self._update_collapse_icon()
                self._collapse_btn.clicked.connect(self._toggle_collapse)
                header_layout.addWidget(self._collapse_btn)

            self._main_layout.addWidget(self._header)

        # Content area
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(SPACING["sm"])
        self._main_layout.addWidget(self._content_widget)

        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(SIZES["shadow_blur"])
        shadow.setXOffset(0)
        shadow.setYOffset(SIZES["shadow_offset"])
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

    def _apply_style(self) -> None:
        """Apply the card styling via dynamic property."""
        if self._hover_effect:
            self.setProperty("hover", True)

    def set_badge(self, text: str) -> None:
        """Set the badge text in the header."""
        if hasattr(self, "_badge_label"):
            if text:
                self._badge_label.setText(text)
                self._badge_label.show()
            else:
                self._badge_label.hide()

    def set_badge_color(self, color: str) -> None:
        """Set the badge highlight state."""
        if hasattr(self, "_badge_label"):
            self._badge_label.setProperty("highlight", True)
            self._badge_label.style().polish(self._badge_label)

    def content_layout(self) -> QVBoxLayout:
        """Get the content layout to add widgets."""
        return self._content_layout

    def set_content_margins(self, left: int, top: int, right: int, bottom: int) -> None:
        """Set the card's content margins."""
        self._main_layout.setContentsMargins(left, top, right, bottom)

    def add_widget(self, widget: QWidget) -> None:
        """Add a widget to the card content area."""
        self._content_layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        """Add a layout to the card content area."""
        self._content_layout.addLayout(layout)

    def add_stretch(self) -> None:
        """Add stretch to the content layout."""
        self._content_layout.addStretch()

    def _update_collapse_icon(self) -> None:
        """Update the collapse button icon based on state."""
        if hasattr(self, "_collapse_btn"):
            icon_name = "fa5s.chevron-right" if self._collapsed else "fa5s.chevron-down"
            icon = qta.icon(icon_name, color=COLORS["text"])
            self._collapse_btn.setIcon(icon)

    def _toggle_collapse(self) -> None:
        """Toggle the collapse state."""
        self._collapsed = not self._collapsed
        self._content_widget.setVisible(not self._collapsed)
        self._update_collapse_icon()
        self.collapsed_changed.emit(self._collapsed)

    def is_collapsed(self) -> bool:
        """Return whether the card is collapsed."""
        return self._collapsed

    def set_collapsed(self, collapsed: bool) -> None:
        """Set the collapse state."""
        if self._collapsible and self._collapsed != collapsed:
            self._toggle_collapse()

    def expand(self) -> None:
        """Expand the card if it's collapsible and collapsed."""
        if self._collapsible and self._collapsed:
            self._toggle_collapse()

    def set_collapsible(self, collapsible: bool) -> None:
        """Enable or disable collapsibility. Expands the card when disabling."""
        if not hasattr(self, "_collapse_btn"):
            return
        self._collapsible = collapsible
        self._collapse_btn.setVisible(collapsible)
        if not collapsible and self._collapsed:
            # Force expand when disabling collapsibility
            self._collapsed = False
            self._content_widget.setVisible(True)
            self._update_collapse_icon()
