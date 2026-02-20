"""Upload progress widget with modern styling."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
)

from gui.theme import COLORS, SPACING, RADIUS


class UploadProgressWidget(QWidget):
    """Widget showing upload progress with file name and percentage."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])

        # Status row
        status_layout = QHBoxLayout()
        status_layout.setSpacing(SPACING["sm"])

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text']};
                font-size: 11pt;
            }}
        """)
        status_layout.addWidget(self._status_label)

        status_layout.addStretch()

        self._count_label = QLabel("")
        self._count_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 10pt;
            }}
        """)
        status_layout.addWidget(self._count_label)

        layout.addLayout(status_layout)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setMinimumHeight(28)
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['background']};
                border: none;
                border-radius: {RADIUS['md']}px;
                text-align: center;
                color: {COLORS['text']};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {COLORS['accent']},
                    stop: 1 {COLORS['accent_hover']}
                );
                border-radius: {RADIUS['md']}px;
            }}
        """)
        layout.addWidget(self._progress_bar)

    def set_total(self, total: int) -> None:
        """Set the total number of files."""
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(0)
        self._count_label.setText(f"0 / {total}")
        self._status_label.setText("Starting...")
        self._reset_status_style()

    def update_progress(self, current: int, total: int, filename: str) -> None:
        """Update progress display."""
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)
        self._status_label.setText(f"Uploading: {filename}")
        self._count_label.setText(f"{current} / {total}")
        self._reset_status_style()

    def set_completed(self, success_count: int, total: int) -> None:
        """Mark upload as completed."""
        self._progress_bar.setValue(total)
        self._status_label.setText(f"\u2713 Completed: {success_count} of {total} files uploaded")
        self._status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['success']};
                font-size: 11pt;
                font-weight: bold;
            }}
        """)
        self._count_label.setText("")

        # Update progress bar to green
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['background']};
                border: none;
                border-radius: {RADIUS['md']}px;
                text-align: center;
                color: {COLORS['text']};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['success']};
                border-radius: {RADIUS['md']}px;
            }}
        """)

    def set_error(self, message: str) -> None:
        """Display error state."""
        self._status_label.setText(f"\u2717 Error: {message}")
        self._status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['error']};
                font-size: 11pt;
                font-weight: bold;
            }}
        """)

        # Update progress bar to red
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['background']};
                border: none;
                border-radius: {RADIUS['md']}px;
                text-align: center;
                color: {COLORS['text']};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['error']};
                border-radius: {RADIUS['md']}px;
            }}
        """)

    def reset(self) -> None:
        """Reset to initial state."""
        self._progress_bar.setValue(0)
        self._progress_bar.setMaximum(100)
        self._status_label.setText("Ready")
        self._count_label.setText("")
        self._reset_status_style()
        self._reset_progress_style()

    def _reset_status_style(self) -> None:
        """Reset status label to default style."""
        self._status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text']};
                font-size: 11pt;
            }}
        """)

    def _reset_progress_style(self) -> None:
        """Reset progress bar to default style."""
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['background']};
                border: none;
                border-radius: {RADIUS['md']}px;
                text-align: center;
                color: {COLORS['text']};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {COLORS['accent']},
                    stop: 1 {COLORS['accent_hover']}
                );
                border-radius: {RADIUS['md']}px;
            }}
        """)
