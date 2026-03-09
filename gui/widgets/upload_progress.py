"""Upload progress widget with modern styling."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
)

from gui.theme import SPACING


class UploadProgressWidget(QWidget):
    """Widget showing upload progress with file name and percentage."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cert_info = ""  # Track which certs are being uploaded
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])

        # Status row
        status_layout = QHBoxLayout()
        status_layout.setSpacing(SPACING["sm"])

        self._status_label = QLabel("Ready")
        self._status_label.setObjectName("uploadStatus")
        status_layout.addWidget(self._status_label)

        status_layout.addStretch()

        self._count_label = QLabel("")
        status_layout.addWidget(self._count_label)

        layout.addLayout(status_layout)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("uploadProgress")
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        layout.addWidget(self._progress_bar)

    def set_total(self, total: int, cert_info: str = "") -> None:
        """Set the total number of files and optional cert info."""
        self._cert_info = cert_info
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(0)
        self._count_label.setText(f"0 / {total}")
        if cert_info:
            self._status_label.setText(f"Uploading: {cert_info}")
        else:
            self._status_label.setText("Starting...")
        self._set_state("ready")

    def update_progress(self, current: int, total: int, filename: str) -> None:
        """Update progress display."""
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)
        # Show cert info with filename if available
        if self._cert_info:
            self._status_label.setText(f"Uploading ({self._cert_info}): {filename}")
        else:
            self._status_label.setText(f"Uploading: {filename}")
        self._count_label.setText(f"{current} / {total}")
        self._set_state("ready")

    def set_completed(
        self, success_count: int, total: int, skipped_count: int = 0, failed_count: int = 0
    ) -> None:
        """Mark upload as completed."""
        self._progress_bar.setValue(total)

        if failed_count > 0:
            # Error state - red bar with X icon
            self._status_label.setText(
                f"\u2717 Failed: {failed_count} of {total} files failed"
            )
            self._set_state("error")
        elif skipped_count > 0:
            self._status_label.setText(
                f"\u2713 Completed: {success_count} uploaded, {skipped_count} skipped"
            )
            self._set_state("success")
        else:
            self._status_label.setText(f"\u2713 Completed: {success_count} of {total} files uploaded")
            self._set_state("success")

        self._count_label.setText("")

    def set_error(self, message: str) -> None:
        """Display error state."""
        self._status_label.setText(f"\u2717 Error: {message}")

        # Update state via properties
        self._set_state("error")

    def set_cancelled(self, success_count: int, total: int) -> None:
        """Display cancelled state - yellow warning bar."""
        self._progress_bar.setValue(total)
        self._status_label.setText(
            f"\u26A0 WARNING: {success_count} of {total} files uploaded (upload cancelled by user)"
        )
        self._count_label.setText("")
        self._set_state("warning")

    def reset(self) -> None:
        """Reset to initial state."""
        self._cert_info = ""
        self._progress_bar.setValue(0)
        self._progress_bar.setMaximum(100)
        self._status_label.setText("Ready")
        self._count_label.setText("")
        self._set_state("ready")

    def _set_state(self, state: str) -> None:
        """Set the visual state via properties (ready, success, error)."""
        self._status_label.setProperty("state", state)
        self._progress_bar.setProperty("state", state)
        self._status_label.style().polish(self._status_label)
        self._progress_bar.style().polish(self._progress_bar)
