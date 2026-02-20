"""Centralized theme system with design tokens."""

from pathlib import Path

import qtawesome as qta
from PySide6.QtGui import QIcon

# Assets directory
ASSETS_DIR = Path(__file__).parent / "assets"


# Color palette
COLORS = {
    "background": "#1e1e2e",       # Dark blue-gray
    "surface": "#2a2a3c",          # Card background
    "surface_hover": "#32324a",    # Card hover
    "border": "#3a3a4c",           # Subtle borders
    "text": "#ffffff",             # Primary text
    "text_secondary": "#a0a0b0",   # Secondary text
    "accent": "#00b4d8",           # Teal accent
    "accent_hover": "#00c4eb",     # Teal hover
    "accent_pressed": "#0096b4",   # Teal pressed
    "selection": "#1a5a6e",        # Muted teal for row selection
    "success": "#4ade80",          # Green
    "error": "#f87171",            # Red
    "warning": "#fbbf24",          # Yellow
    "table_alt": "#252535",        # Alternating row
}

# Spacing constants
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
}

# Border radius
RADIUS = {
    "sm": 4,
    "md": 8,
    "lg": 12,
}

# Font sizes
FONT_SIZE = {
    "sm": 9,
    "md": 10,
    "lg": 12,
    "xl": 14,
}


def get_stylesheet() -> str:
    """Generate the global application stylesheet."""
    # Get absolute path to checkmark asset (Qt requires forward slashes)
    checkmark_path = (ASSETS_DIR / "checkmark.png").resolve().as_posix()

    return f"""
        /* Global styles */
        QMainWindow, QDialog {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
        }}

        /* Menu bar */
        QMenuBar {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border-bottom: 1px solid {COLORS['border']};
            padding: 4px;
        }}

        QMenuBar::item {{
            padding: 6px 12px;
            border-radius: {RADIUS['sm']}px;
        }}

        QMenuBar::item:selected {{
            background-color: {COLORS['surface_hover']};
        }}

        QMenu {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['sm']}px;
            padding: 4px;
        }}

        QMenu::item {{
            padding: 8px 24px;
            border-radius: {RADIUS['sm']}px;
        }}

        QMenu::item:selected {{
            background-color: {COLORS['accent']};
            color: {COLORS['text']};
        }}

        /* Buttons */
        QPushButton {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['md']}px;
            padding: 8px 16px;
            font-weight: 500;
            min-height: 14px;
        }}

        QPushButton:hover {{
            background-color: {COLORS['surface_hover']};
            border-color: {COLORS['accent']};
        }}

        QPushButton:pressed {{
            background-color: {COLORS['border']};
        }}

        QPushButton:disabled {{
            background-color: {COLORS['surface']};
            color: {COLORS['text_secondary']};
            border-color: {COLORS['border']};
        }}

        /* Primary button style class */
        QPushButton[primary="true"] {{
            background-color: {COLORS['accent']};
            border-color: {COLORS['accent']};
            color: #000000;
            font-weight: bold;
        }}

        QPushButton[primary="true"]:hover {{
            background-color: {COLORS['accent_hover']};
            border-color: {COLORS['accent_hover']};
        }}

        QPushButton[primary="true"]:pressed {{
            background-color: {COLORS['accent_pressed']};
        }}

        QPushButton[primary="true"]:disabled {{
            background-color: {COLORS['border']};
            border-color: {COLORS['border']};
            color: {COLORS['text_secondary']};
        }}

        /* Line edits */
        QLineEdit {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['md']}px;
            padding: 8px 12px;
            selection-background-color: {COLORS['accent']};
        }}

        QLineEdit:focus {{
            border-color: {COLORS['accent']};
        }}

        QLineEdit:disabled {{
            background-color: {COLORS['background']};
            color: {COLORS['text_secondary']};
        }}

        /* Checkboxes */
        QCheckBox {{
            color: {COLORS['text']};
            spacing: 8px;
        }}

        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {COLORS['border']};
            border-radius: {RADIUS['sm']}px;
            background-color: {COLORS['surface']};
        }}

        QCheckBox::indicator:hover {{
            border-color: {COLORS['accent']};
        }}

        QCheckBox::indicator:checked {{
            background-color: {COLORS['accent']};
            border-color: {COLORS['accent']};
            image: url({checkmark_path});
        }}

        /* Tables */
        QTableWidget {{
            background-color: {COLORS['surface']};
            alternate-background-color: {COLORS['table_alt']};
            color: {COLORS['text']};
            border: none;
            border-radius: {RADIUS['md']}px;
            gridline-color: {COLORS['border']};
            selection-background-color: {COLORS['selection']};
            selection-color: {COLORS['text']};
        }}

        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {COLORS['border']};
        }}

        QTableWidget::item:selected {{
            background-color: {COLORS['selection']};
            color: {COLORS['text']};
        }}

        QHeaderView::section {{
            background-color: {COLORS['background']};
            color: {COLORS['text_secondary']};
            border: none;
            border-bottom: 2px solid {COLORS['accent']};
            padding: 10px 8px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: {FONT_SIZE['sm']}pt;
        }}

        QTableWidget QTableCornerButton::section {{
            background-color: {COLORS['background']};
            border: none;
        }}

        /* Scrollbars */
        QScrollBar:vertical {{
            background-color: {COLORS['background']};
            width: 12px;
            border-radius: 6px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background-color: {COLORS['border']};
            border-radius: 6px;
            min-height: 30px;
            margin: 2px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['surface_hover']};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        QScrollBar:horizontal {{
            background-color: {COLORS['background']};
            height: 12px;
            border-radius: 6px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {COLORS['border']};
            border-radius: 6px;
            min-width: 30px;
            margin: 2px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {COLORS['surface_hover']};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}

        /* Progress bar */
        QProgressBar {{
            background-color: {COLORS['background']};
            border: 1px solid rgba(0, 0, 0, 0.3);
            border-radius: {RADIUS['md']}px;
            text-align: center;
            color: {COLORS['text']};
            min-height: 24px;
        }}

        QProgressBar::chunk {{
            background-color: {COLORS['accent']};
            border-radius: {RADIUS['md']}px;
        }}

        /* Tab widget */
        QTabWidget::pane {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['md']}px;
            padding: 12px;
        }}

        QTabBar::tab {{
            background-color: {COLORS['background']};
            color: {COLORS['text_secondary']};
            border: none;
            padding: 10px 20px;
            margin-right: 4px;
            border-top-left-radius: {RADIUS['md']}px;
            border-top-right-radius: {RADIUS['md']}px;
        }}

        QTabBar::tab:selected {{
            background-color: {COLORS['surface']};
            color: {COLORS['accent']};
        }}

        QTabBar::tab:hover:!selected {{
            background-color: {COLORS['surface_hover']};
            color: {COLORS['text']};
        }}

        /* Spin box */
        QSpinBox {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['md']}px;
            padding: 6px 12px;
        }}

        QSpinBox:focus {{
            border-color: {COLORS['accent']};
        }}

        QSpinBox::up-button, QSpinBox::down-button {{
            background-color: {COLORS['surface_hover']};
            border: none;
            width: 20px;
        }}

        /* Combo box */
        QComboBox {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['md']}px;
            padding: 6px 12px;
            min-height: 20px;
        }}

        QComboBox:focus {{
            border-color: {COLORS['accent']};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            selection-background-color: {COLORS['accent']};
            selection-color: #000000;
        }}

        /* Labels */
        QLabel {{
            color: {COLORS['text']};
        }}

        /* Dialog button box */
        QDialogButtonBox {{
            button-layout: 3;
        }}

        /* Message box */
        QMessageBox {{
            background-color: {COLORS['surface']};
        }}

        QMessageBox QLabel {{
            color: {COLORS['text']};
        }}
    """


def get_card_style(hover: bool = True) -> str:
    """Get stylesheet for card widgets."""
    hover_style = f"""
        Card:hover {{
            background-color: {COLORS['surface_hover']};
            border-color: {COLORS['accent']};
        }}
    """ if hover else ""

    return f"""
        Card {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['lg']}px;
        }}
        {hover_style}
    """


# Icon definitions using Font Awesome
ICONS = {
    "search": "fa5s.search",
    "certificate": "fa5s.clipboard-list",
    "upload": "fa5s.cloud-upload-alt",
    "log": "fa5s.stream",
    "database": "fa5s.database",
    "box": "fa5s.box",
    "folder": "fa5s.folder-open",
    "plug": "fa5s.plug",
    "check": "fa5s.check",
    "times": "fa5s.times",
    "warning": "fa5s.exclamation-triangle",
    "info": "fa5s.info-circle",
    "settings": "fa5s.cog",
    "file": "fa5s.file-alt",
}


def get_icon(name: str, color: str | None = None, size: int = 16) -> QIcon:
    """Get a themed icon by name.

    Args:
        name: Icon name from ICONS dict, or direct Font Awesome icon name
        color: Icon color (defaults to accent color)
        size: Icon size in pixels

    Returns:
        QIcon instance
    """
    icon_name = ICONS.get(name, name)
    icon_color = color or COLORS["accent"]
    return qta.icon(icon_name, color=icon_color, scale_factor=1.0)
