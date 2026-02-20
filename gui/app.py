"""Application entry point with modern dark theme."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QIcon
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.theme import COLORS, get_stylesheet


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


def apply_dark_theme(app: QApplication) -> None:
    """Apply the modern dark theme to the application."""
    app.setStyle("Fusion")

    # Set color palette
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

    apply_dark_theme(app)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(launch_app())
