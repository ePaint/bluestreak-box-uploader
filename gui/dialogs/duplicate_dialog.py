"""Dialog for handling duplicate file detection during upload."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QWidget,
)

from database.models import DuplicateAction
from gui.theme import COLORS, FONT_SIZE, SPACING, RADIUS, get_icon


class DuplicateFileDialog(QDialog):
    """Dialog shown when a duplicate file is detected during upload."""

    def __init__(self, filename: str, cert_no: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Already Exists")
        self.setModal(True)
        self.setMinimumWidth(400)

        self._action: DuplicateAction = DuplicateAction.CANCEL
        self._apply_to_all: bool = False

        self._setup_ui(filename, cert_no)

    def _setup_ui(self, filename: str, cert_no: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        # Header with warning icon
        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACING["sm"])

        icon_label = QLabel()
        icon = get_icon("warning", COLORS["warning"], 24)
        icon_label.setPixmap(icon.pixmap(24, 24))
        header_layout.addWidget(icon_label)

        title_label = QLabel("File Already Exists")
        title_label.setStyleSheet(f"""
            font-size: {FONT_SIZE['lg']}pt;
            font-weight: bold;
            color: {COLORS['warning']};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Message
        message = QLabel(f'"{filename}" already exists in Box.\n\nCertification: {cert_no}\n\nWhat would you like to do?')
        message.setWordWrap(True)
        message.setStyleSheet(f"""
            font-size: {FONT_SIZE['md']}pt;
            color: {COLORS['text']};
            padding: {SPACING['sm']}px 0;
        """)
        layout.addWidget(message)

        # Apply to all checkbox
        self._apply_all_checkbox = QCheckBox("Apply to all remaining duplicates")
        layout.addWidget(self._apply_all_checkbox)

        layout.addSpacing(SPACING["sm"])

        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(SPACING["sm"])
        button_layout.addStretch()

        # Replace button (primary action)
        replace_btn = QPushButton("Replace")
        replace_btn.setProperty("primary", True)
        replace_btn.setMinimumWidth(90)
        replace_btn.clicked.connect(self._on_replace)
        button_layout.addWidget(replace_btn)

        # Skip button
        skip_btn = QPushButton("Skip")
        skip_btn.setMinimumWidth(90)
        skip_btn.clicked.connect(self._on_skip)
        button_layout.addWidget(skip_btn)

        # Cancel button
        cancel_btn = QPushButton("Cancel All")
        cancel_btn.setMinimumWidth(90)
        cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # Style the dialog background
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['surface']};
            }}
        """)

    def _on_replace(self) -> None:
        self._action = DuplicateAction.REPLACE
        self._apply_to_all = self._apply_all_checkbox.isChecked()
        self.accept()

    def _on_skip(self) -> None:
        self._action = DuplicateAction.SKIP
        self._apply_to_all = self._apply_all_checkbox.isChecked()
        self.accept()

    def _on_cancel(self) -> None:
        self._action = DuplicateAction.CANCEL
        self._apply_to_all = False
        self.reject()

    @property
    def action(self) -> DuplicateAction:
        """Get the user's selected action."""
        return self._action

    @property
    def apply_to_all(self) -> bool:
        """Get whether to apply the action to all remaining duplicates."""
        return self._apply_to_all
