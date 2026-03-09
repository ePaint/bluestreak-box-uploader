"""Log viewer widget with modern styling."""

from datetime import datetime

from PySide6.QtWidgets import QTextEdit

from gui.theme import COLORS


class LogViewer(QTextEdit):
    """Read-only text widget for displaying log messages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logViewer")
        self.setReadOnly(True)

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
