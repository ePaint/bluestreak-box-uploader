"""Upload progress widget."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
)


class UploadProgressWidget(QWidget):
    """Widget showing upload progress with file name and percentage."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Status row
        status_layout = QHBoxLayout()

        self._status_label = QLabel("Ready")
        status_layout.addWidget(self._status_label)

        status_layout.addStretch()

        self._count_label = QLabel("")
        status_layout.addWidget(self._count_label)

        layout.addLayout(status_layout)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        layout.addWidget(self._progress_bar)

    def set_total(self, total: int) -> None:
        """Set the total number of files."""
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(0)
        self._count_label.setText(f"0 / {total}")

    def update_progress(self, current: int, total: int, filename: str) -> None:
        """Update progress display."""
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)
        self._status_label.setText(f"Uploading: {filename}")
        self._count_label.setText(f"{current} / {total}")

    def set_completed(self, success_count: int, total: int) -> None:
        """Mark upload as completed."""
        self._progress_bar.setValue(total)
        self._status_label.setText(f"Completed: {success_count} of {total} files uploaded")
        self._count_label.setText("")

    def set_error(self, message: str) -> None:
        """Display error state."""
        self._status_label.setText(f"Error: {message}")
        self._status_label.setStyleSheet("color: #ff6b6b;")

    def reset(self) -> None:
        """Reset to initial state."""
        self._progress_bar.setValue(0)
        self._progress_bar.setMaximum(100)
        self._status_label.setText("Ready")
        self._status_label.setStyleSheet("")
        self._count_label.setText("")
