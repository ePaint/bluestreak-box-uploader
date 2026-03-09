"""Centralized theme system with design tokens."""

from pathlib import Path

import qtawesome as qta
from PySide6.QtGui import QIcon

# Assets directory
ASSETS_DIR = Path(__file__).parent / "assets"


# Color palettes
COLORS_DARK = {
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

COLORS_LIGHT = {
    "background": "#f5f5f7",       # Light gray
    "surface": "#ffffff",          # White card background
    "surface_hover": "#e8e8ed",    # Card hover
    "border": "#d1d1d6",           # Subtle borders
    "text": "#1d1d1f",             # Primary text (dark)
    "text_secondary": "#6e6e73",   # Secondary text
    "accent": "#0071e3",           # Blue accent
    "accent_hover": "#0077ed",     # Blue hover
    "accent_pressed": "#005bb5",   # Blue pressed
    "selection": "#b3d7ff",        # Light blue for row selection
    "success": "#28a745",          # Green
    "error": "#dc3545",            # Red
    "warning": "#f5a623",          # Yellow/orange
    "table_alt": "#f0f0f5",        # Alternating row
}

# Default to dark theme (will be set by app.py based on settings)
COLORS = COLORS_DARK.copy()

# Base spacing constants (scaled by set_ui_scale)
SPACING_BASE = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
}

# Base border radius (scaled by set_ui_scale)
RADIUS_BASE = {
    "sm": 4,
    "md": 8,
    "lg": 12,
}

# Base sizes for UI elements (scaled by set_ui_scale)
SIZES_BASE = {
    # Window
    "window_min_w": 850, "window_min_h": 750,
    "window_default_w": 900, "window_default_h": 1000,
    "wide_threshold": 1200,

    # Dialogs
    "dialog_min_w": 550, "dialog_min_h": 400, "dialog_small_w": 400,

    # Inputs/Buttons
    "input_max_w": 300, "input_min_w": 200,
    "btn_w_lg": 140, "btn_w_md": 120, "btn_w_sm": 100, "btn_w_xs": 90,
    "btn_max_h": 36, "filter_w": 100, "label_min_w": 40,

    # Heights
    "table_min_h": 200, "log_min_h": 100, "history_min_h": 150, "warning_min_h": 50,

    # Icons
    "icon_sm": 16, "icon_md": 20, "icon_lg": 24,

    # Stylesheet elements
    "checkbox": 18, "scrollbar_w": 12, "scrollbar_r": 6, "scrollbar_min_h": 30,
    "slider_groove": 6, "slider_handle": 16,
    "tree_indent": 20, "tree_row_h": 28,
    "combo_min_h": 20, "combo_dropdown_w": 30,
    "shadow_blur": 20, "shadow_offset": 4,
    "collapse_btn": 24, "splitter_default": 500,

    # Column defaults
    "col_cert": 140, "col_customer": 200, "col_po": 100, "col_date": 90, "col_files": 50,

    # History columns
    "hist_col_time": 60, "hist_col_order": 70, "hist_col_cert": 100,
    "hist_col_customer": 120, "hist_col_po": 80, "hist_col_filename": 150,
    "hist_col_status": 50, "hist_col_error": 120,
}

# Active spacing/radius/sizes (updated by set_ui_scale)
SPACING = SPACING_BASE.copy()
RADIUS = RADIUS_BASE.copy()
SIZES = SIZES_BASE.copy()
_ui_scale_factor = 1.0

# Base font sizes (will be scaled by font_size setting)
FONT_SIZE_BASE = {
    "xs": 8,   # Help text
    "sm": 9,   # Small labels
    "md": 10,  # Default text
    "lg": 12,  # Card titles
    "xl": 14,  # Emphasized text
    "xxl": 18, # Order input (large)
}

# Current font sizes (updated by set_font_scale)
FONT_SIZE = FONT_SIZE_BASE.copy()


def set_theme(theme: str) -> None:
    """Set the active color theme.

    Args:
        theme: 'dark' or 'light'
    """
    global COLORS
    if theme == "light":
        COLORS.clear()
        COLORS.update(COLORS_LIGHT)
    else:
        COLORS.clear()
        COLORS.update(COLORS_DARK)


def set_font_scale(base_size: int) -> None:
    """Set the font scale based on a base size.

    Args:
        base_size: Base font size (default 10, range 8-16)
    """
    global FONT_SIZE
    scale = base_size / 10.0
    FONT_SIZE["xs"] = int(FONT_SIZE_BASE["xs"] * scale)
    FONT_SIZE["sm"] = int(FONT_SIZE_BASE["sm"] * scale)
    FONT_SIZE["md"] = int(FONT_SIZE_BASE["md"] * scale)
    FONT_SIZE["lg"] = int(FONT_SIZE_BASE["lg"] * scale)
    FONT_SIZE["xl"] = int(FONT_SIZE_BASE["xl"] * scale)
    FONT_SIZE["xxl"] = int(FONT_SIZE_BASE["xxl"] * scale)


def set_ui_scale(scale: int) -> None:
    """Set UI scale (100, 125, or 150).

    Args:
        scale: Scale percentage (100, 125, or 150)
    """
    global SIZES, SPACING, RADIUS, _ui_scale_factor
    _ui_scale_factor = scale / 100.0

    SIZES.clear()
    for k, v in SIZES_BASE.items():
        SIZES[k] = int(v * _ui_scale_factor)

    SPACING.clear()
    for k, v in SPACING_BASE.items():
        SPACING[k] = int(v * _ui_scale_factor)

    RADIUS.clear()
    for k, v in RADIUS_BASE.items():
        RADIUS[k] = int(v * _ui_scale_factor)


def get_stylesheet() -> str:
    """Generate the global application stylesheet."""
    # Get absolute path to checkmark asset (Qt requires forward slashes)
    checkmark_path = (ASSETS_DIR / "checkmark.png").resolve().as_posix()
    dash_path = (ASSETS_DIR / "dash.png").resolve().as_posix()
    arrow_down_path = (ASSETS_DIR / "arrow_down.png").resolve().as_posix()

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
            font-size: {FONT_SIZE['md']}pt;
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
            font-size: {FONT_SIZE['md']}pt;
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
            padding: {FONT_SIZE['sm']}px {FONT_SIZE['xl']}px;
            font-size: {FONT_SIZE['md']}pt;
            font-weight: 500;
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
            font-size: {FONT_SIZE['md']}pt;
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
            font-size: {FONT_SIZE['md']}pt;
            spacing: {SPACING['sm']}px;
        }}

        QCheckBox::indicator {{
            width: {SIZES['checkbox']}px;
            height: {SIZES['checkbox']}px;
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
            font-size: {FONT_SIZE['md']}pt;
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
            width: {SIZES['scrollbar_w']}px;
            border-radius: {SIZES['scrollbar_r']}px;
            margin: 0;
        }}

        QScrollBar::handle:vertical {{
            background-color: {COLORS['border']};
            border-radius: {SIZES['scrollbar_r']}px;
            min-height: {SIZES['scrollbar_min_h']}px;
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
            height: {SIZES['scrollbar_w']}px;
            border-radius: {SIZES['scrollbar_r']}px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {COLORS['border']};
            border-radius: {SIZES['scrollbar_r']}px;
            min-width: {SIZES['scrollbar_min_h']}px;
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
            font-size: {FONT_SIZE['md']}pt;
            padding: {FONT_SIZE['xs']}px;
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
            font-size: {FONT_SIZE['md']}pt;
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

        /* Spin box - styled like text input, no arrows */
        QSpinBox {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['md']}px;
            padding: 6px 12px;
            font-size: {FONT_SIZE['md']}pt;
        }}

        QSpinBox:focus {{
            border-color: {COLORS['accent']};
        }}

        QSpinBox::up-button, QSpinBox::down-button {{
            width: 0;
            border: none;
        }}

        /* Combo box */
        QComboBox {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['md']}px;
            padding: 6px 12px;
            font-size: {FONT_SIZE['md']}pt;
            min-height: {SIZES['combo_min_h']}px;
        }}

        QComboBox:focus {{
            border-color: {COLORS['accent']};
        }}

        QComboBox::drop-down {{
            border: none;
            width: {SIZES['combo_dropdown_w']}px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            selection-background-color: {COLORS['accent']};
            selection-color: #000000;
        }}

        /* Date edit */
        QDateEdit {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['md']}px;
            padding: 6px 12px;
            font-size: {FONT_SIZE['md']}pt;
            min-height: {SIZES['combo_min_h']}px;
        }}

        QDateEdit:focus {{
            border-color: {COLORS['accent']};
        }}

        QDateEdit:disabled {{
            background-color: {COLORS['background']};
            color: {COLORS['text_secondary']};
        }}

        QDateEdit::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 20px;
            border: none;
        }}

        QDateEdit::down-arrow {{
            image: url({arrow_down_path});
            width: 12px;
            height: 12px;
        }}

        /* Calendar popup */
        QCalendarWidget {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
        }}

        QCalendarWidget QToolButton {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: none;
            padding: 4px;
        }}

        QCalendarWidget QToolButton:hover {{
            background-color: {COLORS['surface_hover']};
        }}

        QCalendarWidget QMenu {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
        }}

        QCalendarWidget QSpinBox {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
        }}

        QCalendarWidget QAbstractItemView:enabled {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            selection-background-color: {COLORS['accent']};
            selection-color: #000000;
        }}

        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: {COLORS['background']};
        }}

        /* Slider */
        QSlider::groove:horizontal {{
            background-color: {COLORS['border']};
            height: {SIZES['slider_groove']}px;
            border-radius: {int(SIZES['slider_groove'] / 2)}px;
        }}

        QSlider::handle:horizontal {{
            background-color: {COLORS['accent']};
            width: {SIZES['slider_handle']}px;
            height: {SIZES['slider_handle']}px;
            margin: -{int((SIZES['slider_handle'] - SIZES['slider_groove']) / 2)}px 0;
            border-radius: {int(SIZES['slider_handle'] / 2)}px;
        }}

        QSlider::handle:horizontal:hover {{
            background-color: {COLORS['accent_hover']};
        }}

        QSlider::sub-page:horizontal {{
            background-color: {COLORS['accent']};
            border-radius: {int(SIZES['slider_groove'] / 2)}px;
        }}

        /* Labels */
        QLabel {{
            color: {COLORS['text']};
            font-size: {FONT_SIZE['md']}pt;
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

        /* === COMPONENT-SPECIFIC STYLES === */

        /* Tab widget - underline style for cards */
        QTabWidget#logTabs::pane {{
            border: none;
            background: transparent;
        }}
        QTabWidget#logTabs QTabBar::tab {{
            background: transparent;
            color: {COLORS['text_secondary']};
            border: none;
            border-bottom: 2px solid transparent;
            padding: 8px 16px;
        }}
        QTabWidget#logTabs QTabBar::tab:selected {{
            color: {COLORS['accent']};
            border-bottom-color: {COLORS['accent']};
        }}
        QTabWidget#logTabs QTabBar::tab:hover:!selected {{
            color: {COLORS['text']};
        }}

        /* Order input (objectName: orderInput) */
        QLineEdit#orderInput {{
            font-size: {FONT_SIZE['xxl']}pt;
            font-weight: bold;
            padding: {FONT_SIZE['lg']}px {FONT_SIZE['xl']}px;
            border: 2px solid {COLORS['border']};
            border-radius: 8px;
        }}
        QLineEdit#orderInput:focus {{
            border-color: {COLORS['accent']};
        }}

        /* Warning label (objectName: warningLabel) */
        QLabel#warningLabel {{
            color: {COLORS['warning']};
            background: rgba(251, 191, 36, 0.15);
            padding: 12px;
            border-radius: 8px;
            border: 1px solid rgba(251, 191, 36, 0.3);
        }}

        /* Card components */
        QLabel#cardTitle {{
            font-size: {FONT_SIZE['lg']}pt;
            font-weight: bold;
            letter-spacing: 0.5px;
        }}
        QLabel#cardBadge {{
            color: {COLORS['text_secondary']};
            font-size: {FONT_SIZE['md']}pt;
            background: {COLORS['background']};
            padding: 4px 8px;
            border-radius: {RADIUS['sm']}px;
        }}
        QLabel#cardBadge[highlight="true"] {{
            color: {COLORS['text']};
        }}
        QPushButton#collapseBtn {{
            background: transparent;
            border: none;
        }}

        /* Card frame */
        Card {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['lg']}px;
        }}
        Card[hover="true"]:hover {{
            background-color: {COLORS['surface_hover']};
            border-color: {COLORS['accent']};
        }}

        /* Tree widgets (QTreeWidget common style) */
        QTreeWidget {{
            background: {COLORS['background']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['md']}px;
        }}
        QTreeWidget::item {{
            padding: {SPACING['xs']}px;
            min-height: {SIZES['tree_row_h']}px;
            font-size: {FONT_SIZE['md']}pt;
        }}
        QTreeWidget::item:selected {{
            background: {COLORS['selection']};
        }}
        QTreeWidget::indicator {{
            width: {SIZES['checkbox']}px;
            height: {SIZES['checkbox']}px;
            border: 2px solid {COLORS['border']};
            border-radius: {RADIUS['sm']}px;
            background-color: {COLORS['surface']};
        }}
        QTreeWidget::indicator:hover {{
            border-color: {COLORS['accent']};
        }}
        QTreeWidget::indicator:checked {{
            background-color: {COLORS['accent']};
            border-color: {COLORS['accent']};
            image: url({checkmark_path});
        }}
        QTreeWidget::indicator:indeterminate {{
            background-color: {COLORS['accent']};
            border-color: {COLORS['accent']};
            image: url({dash_path});
        }}

        /* Log viewer (QTextEdit#logViewer) */
        QTextEdit#logViewer {{
            background: {COLORS['background']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS['md']}px;
            font-family: 'Cascadia Code', 'Consolas', monospace;
            padding: 8px;
        }}

        /* Upload progress states (using properties) */
        QLabel#uploadStatus {{
            font-size: {FONT_SIZE['md']}pt;
        }}
        QLabel#uploadStatus[state="success"] {{
            color: {COLORS['success']};
            font-weight: bold;
        }}
        QLabel#uploadStatus[state="error"] {{
            color: {COLORS['error']};
            font-weight: bold;
        }}
        QProgressBar#uploadProgress {{
            background-color: {COLORS['background']};
            border: none;
            border-radius: {RADIUS['md']}px;
            text-align: center;
            font-size: {FONT_SIZE['md']}pt;
            font-weight: bold;
            padding: {FONT_SIZE['xs']}px;
        }}
        QProgressBar#uploadProgress::chunk {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {COLORS['accent']},
                stop: 1 {COLORS['accent_hover']}
            );
            border-radius: {RADIUS['md']}px;
        }}
        QProgressBar#uploadProgress[state="success"]::chunk {{
            background: {COLORS['success']};
        }}
        QProgressBar#uploadProgress[state="error"]::chunk {{
            background: {COLORS['error']};
        }}

        /* Help labels (objectName: helpLabel) */
        QLabel#helpLabel {{
            color: {COLORS['text_secondary']};
            font-size: {FONT_SIZE['xs']}pt;
            padding: 8px;
            background: {COLORS['background']};
            border-radius: {RADIUS['sm']}px;
        }}
    """


# Icon definitions using Font Awesome
ICONS = {
    "search": "fa5s.search",
    "certificate": "fa5s.clipboard-list",
    "upload": "fa5s.cloud-upload-alt",
    "log": "fa5s.stream",
    "history": "fa5s.history",
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
