"""Reusable card widget with rounded corners and shadow effect."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QColor, QIcon

from gui.theme import COLORS, SPACING, RADIUS


class Card(QFrame):
    """Modern card container with rounded corners and optional header."""

    def __init__(
        self,
        title: str = "",
        icon: QIcon | None = None,
        parent: QWidget | None = None,
        hover_effect: bool = False,
    ):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._hover_effect = hover_effect
        self._setup_ui()
        self._apply_style()

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
                self._icon_label.setPixmap(self._icon.pixmap(16, 16))
                self._icon_label.setFixedSize(20, 20)
                self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                header_layout.addWidget(self._icon_label)

            # Title
            self._title_label = QLabel(self._title)
            self._title_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['text']};
                    font-size: 12px;
                    font-weight: bold;
                    letter-spacing: 0.5px;
                }}
            """)
            header_layout.addWidget(self._title_label)

            # Badge placeholder (right side)
            self._badge_label = QLabel()
            self._badge_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['text_secondary']};
                    font-size: 11px;
                    background-color: {COLORS['background']};
                    padding: 4px 8px;
                    border-radius: {RADIUS['sm']}px;
                }}
            """)
            self._badge_label.hide()
            header_layout.addStretch()
            header_layout.addWidget(self._badge_label)

            self._main_layout.addWidget(self._header)

        # Content area
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(SPACING["sm"])
        self._main_layout.addWidget(self._content_widget)

        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

    def _apply_style(self) -> None:
        """Apply the card styling."""
        hover_style = ""
        if self._hover_effect:
            hover_style = f"""
                Card:hover {{
                    background-color: {COLORS['surface_hover']};
                    border-color: {COLORS['accent']};
                }}
            """

        self.setStyleSheet(f"""
            Card {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS['lg']}px;
            }}
            {hover_style}
        """)

    def set_badge(self, text: str) -> None:
        """Set the badge text in the header."""
        if hasattr(self, "_badge_label"):
            if text:
                self._badge_label.setText(text)
                self._badge_label.show()
            else:
                self._badge_label.hide()

    def set_badge_color(self, color: str) -> None:
        """Set the badge background color."""
        if hasattr(self, "_badge_label"):
            self._badge_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['text']};
                    font-size: 11px;
                    background-color: {color};
                    padding: 4px 8px;
                    border-radius: {RADIUS['sm']}px;
                }}
            """)

    def content_layout(self) -> QVBoxLayout:
        """Get the content layout to add widgets."""
        return self._content_layout

    def add_widget(self, widget: QWidget) -> None:
        """Add a widget to the card content area."""
        self._content_layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        """Add a layout to the card content area."""
        self._content_layout.addLayout(layout)

    def add_stretch(self) -> None:
        """Add stretch to the content layout."""
        self._content_layout.addStretch()
