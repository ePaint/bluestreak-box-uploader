"""About dialog showing application version and info."""

import re
import sys
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from gui.theme import COLORS, SPACING, SIZES, get_icon


def get_app_version() -> str:
    """Get application version from package metadata or pyproject.toml."""
    try:
        return version("bluestreak-box-uploader")
    except PackageNotFoundError:
        # Fallback: read from pyproject.toml
        pyproject = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject.exists():
            match = re.search(r'version\s*=\s*"([^"]+)"', pyproject.read_text())
            if match:
                return match.group(1)
        return "dev"


class AboutDialog(QDialog):
    """Dialog showing application information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setModal(True)
        self.setMinimumWidth(SIZES["dialog_small_w"])
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
        layout.setSpacing(SPACING["md"])

        # Header with app icon
        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACING["md"])

        icon_label = QLabel()
        icon = get_icon("box", COLORS["accent"], SIZES["icon_lg"])
        icon_label.setPixmap(icon.pixmap(SIZES["icon_lg"], SIZES["icon_lg"]))
        header_layout.addWidget(icon_label)

        title_label = QLabel("Bluestreak Box Uploader")
        title_label.setObjectName("aboutTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Version
        version_label = QLabel(f"Version {get_app_version()}")
        version_label.setObjectName("aboutVersion")
        layout.addWidget(version_label)

        layout.addSpacing(SPACING["sm"])

        # Description
        desc_label = QLabel("Upload certifications to Box.com from Bluestreak database.")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addSpacing(SPACING["md"])

        # System info
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        info_label = QLabel(f"Python {python_version}")
        info_label.setObjectName("aboutInfo")
        layout.addWidget(info_label)

        layout.addStretch()

        # OK button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setProperty("primary", True)
        ok_btn.setMinimumWidth(SIZES["btn_w_xs"])
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)
