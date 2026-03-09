"""Application entry point with modern theme support."""

import sys
import os
from pathlib import Path

# Suppress Shiboken conversion warnings in PySide6 6.10.x
# See: https://github.com/angr/angr-management/issues/1514
os.environ.setdefault("QT_LOGGING_RULES", "qt.pysideplugin.warning=false")

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QIcon
from PySide6.QtWidgets import QApplication

from database.history import init_history_db
from gui.main_window import MainWindow
from gui.theme import COLORS, get_stylesheet, set_theme, set_font_scale, set_ui_scale
from settings import load_settings


def get_icon_path() -> Path | None:
    """Get path to app icon, checking multiple locations."""
    # PyInstaller stores bundled files in sys._MEIPASS
    if hasattr(sys, "_MEIPASS"):
        bundled = Path(sys._MEIPASS) / "app.ico"
        if bundled.exists():
            return bundled

    candidates = [
        Path(__file__).parent.parent / "app.ico",  # Development: project root
        Path(sys.executable).parent / "app.ico",   # PyInstaller: next to exe
        Path(__file__).parent / "app.ico",         # Fallback: gui folder
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def apply_theme(app: QApplication) -> None:
    """Apply the theme from settings to the application."""
    # Load settings and apply theme/font/scale before building UI
    settings = load_settings()
    theme = settings.theme
    font_size = settings.font_size
    ui_scale = settings.ui_scale

    set_theme(theme)
    set_font_scale(font_size)
    set_ui_scale(ui_scale)

    app.setStyle("Fusion")

    # Set color palette based on current COLORS (set by set_theme)
    palette = QPalette()

    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS["background"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLORS["surface"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS["table_alt"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLORS["surface"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(COLORS["text"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLORS["text"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(COLORS["surface"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS["text"]))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(COLORS["error"]))
    palette.setColor(QPalette.ColorRole.Link, QColor(COLORS["accent"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS["accent"]))

    # Set highlighted text color based on theme
    if theme == "light":
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    else:
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor(COLORS["text_secondary"]),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor(COLORS["text_secondary"]),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor(COLORS["text_secondary"]),
    )

    app.setPalette(palette)

    # Apply global stylesheet
    app.setStyleSheet(get_stylesheet())


def launch_app() -> int:
    """Launch the application and return exit code."""
    app = QApplication(sys.argv)
    app.setApplicationName("Bluestreak Box Uploader")
    app.setApplicationDisplayName("Bluestreak Box Uploader")
    app.setDesktopFileName("Bluestreak Box Uploader")

    icon_path = get_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))

    apply_theme(app)

    # Initialize history database and cleanup old entries
    init_history_db()
    from database.history import cleanup_old_history

    cleanup_old_history()

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(launch_app())
