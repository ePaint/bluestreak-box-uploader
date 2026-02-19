"""Log viewer widget."""

from datetime import datetime

from PySide6.QtWidgets import QTextEdit


class LogViewer(QTextEdit):
    """Read-only text widget for displaying log messages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #444;
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 9pt;
            }
        """)

    def log(self, message: str, timestamp: bool = True) -> None:
        """Append a log message."""
        if timestamp:
            ts = datetime.now().strftime("%H:%M:%S")
            self.append(f"[{ts}] {message}")
        else:
            self.append(message)

    def log_error(self, message: str) -> None:
        """Append an error message in red."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.append(f'<span style="color: #ff6b6b;">[{ts}] ERROR: {message}</span>')

    def log_success(self, message: str) -> None:
        """Append a success message in green."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.append(f'<span style="color: #69db7c;">[{ts}] {message}</span>')

    def log_warning(self, message: str) -> None:
        """Append a warning message in yellow."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.append(f'<span style="color: #ffd43b;">[{ts}] WARNING: {message}</span>')
