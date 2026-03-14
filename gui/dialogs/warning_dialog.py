"""Reusable warning dialog with styled header and Yes/No buttons."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from gui.theme import COLORS, SPACING, SIZES, get_icon


class WarningDialog(QDialog):
    """Warning dialog matching the styled look of DuplicateFileDialog.

    Features:
    - Yellow warning icon and title
    - Configurable message
    - No/Yes buttons (Yes on right as primary/default)

    Usage:
        dialog = WarningDialog("Title", "Message", parent)
        if dialog.exec():
            # User clicked Yes
        else:
            # User clicked No or closed dialog
    """

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(SIZES["dialog_small_w"])
        self._setup_ui(title, message)

    def _setup_ui(self, title: str, message: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        # Header with warning icon
        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACING["sm"])

        icon_label = QLabel()
        icon = get_icon("warning", COLORS["warning"], SIZES["icon_lg"])
        icon_label.setPixmap(icon.pixmap(SIZES["icon_lg"], SIZES["icon_lg"]))
        header_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setObjectName("warningTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Message
        message_label = QLabel(message)
        message_label.setObjectName("warningMessage")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        layout.addSpacing(SPACING["sm"])

        # Button row: No on left, Yes on right (primary/default)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(SPACING["sm"])
        button_layout.addStretch()

        no_btn = QPushButton("No")
        no_btn.setMinimumWidth(SIZES["btn_w_xs"])
        no_btn.clicked.connect(self.reject)
        button_layout.addWidget(no_btn)

        yes_btn = QPushButton("Yes")
        yes_btn.setProperty("primary", True)
        yes_btn.setMinimumWidth(SIZES["btn_w_xs"])
        yes_btn.clicked.connect(self.accept)
        yes_btn.setDefault(True)
        button_layout.addWidget(yes_btn)

        layout.addLayout(button_layout)
