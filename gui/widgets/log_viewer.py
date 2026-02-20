"""Log viewer widget with modern styling."""

from datetime import datetime

from PySide6.QtWidgets import QTextEdit

from gui.theme import COLORS, RADIUS


class LogViewer(QTextEdit):
    """Read-only text widget for displaying log messages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS['md']}px;
                font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
                font-size: 10pt;
                padding: 8px;
                selection-background-color: {COLORS['accent']};
                selection-color: #000000;
            }}
        """)

    def log(self, message: str, timestamp: bool = True) -> None:
        """Append a log message."""
        if timestamp:
            ts = datetime.now().strftime("%H:%M:%S")
            self.append(f'<span style="color: {COLORS["text_secondary"]};">[{ts}]</span> {message}')
        else:
            self.append(message)

    def log_error(self, message: str) -> None:
        """Append an error message in red."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.append(
            f'<span style="color: {COLORS["text_secondary"]};">[{ts}]</span> '
            f'<span style="color: {COLORS["error"]};">\u2717 ERROR: {message}</span>'
        )

    def log_success(self, message: str) -> None:
        """Append a success message in green."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.append(
            f'<span style="color: {COLORS["text_secondary"]};">[{ts}]</span> '
            f'<span style="color: {COLORS["success"]};">\u2713 {message}</span>'
        )

    def log_warning(self, message: str) -> None:
        """Append a warning message in yellow."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.append(
            f'<span style="color: {COLORS["text_secondary"]};">[{ts}]</span> '
            f'<span style="color: {COLORS["warning"]};">\u26A0 WARNING: {message}</span>'
        )
