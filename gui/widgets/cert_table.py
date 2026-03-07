"""Certification tree with expandable rows and file selection."""

from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QPushButton,
)

from database.models import Certification, MediaFile
from gui.theme import COLORS, SPACING
from settings import load_settings, save_settings


class CertificationTable(QWidget):
    """Tree widget displaying certifications with expandable file rows."""

    selection_changed = Signal()  # Emitted when selection changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self._certifications: list[Certification] = []
        self._updating_checkboxes = False  # Prevent recursion
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])

        # Tree widget
        self._tree = QTreeWidget()
        self._tree.setColumnCount(7)
        self._tree.setHeaderLabels(["Cert No", "Customer", "PO#", "Cert Date", "Added", "Files", ""])
        self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setIndentation(20)
        self._tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Column sizing
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Cert No
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Customer
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # PO#
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Cert Date
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Added
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Files
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)        # Hidden
        self._tree.setColumnHidden(6, True)  # Hide the extra column

        # Restore saved column widths or use defaults
        self._restore_column_widths()

        # Save column widths when user resizes
        header.sectionResized.connect(self._on_column_resized)

        # Connect item changed signal for checkbox handling
        self._tree.itemChanged.connect(self._on_item_changed)

        layout.addWidget(self._tree)

        # Buttons row
        self._btn_layout = QHBoxLayout()
        self._btn_layout.setSpacing(SPACING["sm"])

        self._select_all_btn = QPushButton("Select All")
        self._select_all_btn.clicked.connect(self._select_all)
        self._btn_layout.addWidget(self._select_all_btn)

        self._deselect_all_btn = QPushButton("Clear")
        self._deselect_all_btn.clicked.connect(self._deselect_all)
        self._btn_layout.addWidget(self._deselect_all_btn)

        self._expand_all_btn = QPushButton("Expand All")
        self._expand_all_btn.clicked.connect(self._tree.expandAll)
        self._btn_layout.addWidget(self._expand_all_btn)

        self._collapse_all_btn = QPushButton("Collapse All")
        self._collapse_all_btn.clicked.connect(self._tree.collapseAll)
        self._btn_layout.addWidget(self._collapse_all_btn)

        self._btn_layout.addStretch()

        layout.addLayout(self._btn_layout)

    def add_toolbar_widget(self, widget: QWidget) -> None:
        """Add a widget to the toolbar row (after the stretch)."""
        self._btn_layout.addWidget(widget)

    def set_certifications(
        self, certifications: list[Certification], warning_days: int = 30
    ) -> None:
        """Set the certifications to display.

        Args:
            certifications: List of certifications to display
            warning_days: Days threshold for warning styling (0 = disabled)
        """
        self._certifications = certifications
        self._tree.clear()

        # Pre-compute warning cutoff and brush (avoid creating inside loop)
        warning_cutoff = (
            datetime.now() - timedelta(days=warning_days) if warning_days > 0 else None
        )
        warning_brush = QBrush(QColor(COLORS["warning"])) if warning_cutoff else None

        for cert_idx, cert in enumerate(certifications):
            # Create parent item for certification
            parent_item = QTreeWidgetItem()
            parent_item.setText(0, cert.crt_cert_no)
            parent_item.setText(1, cert.crt_cust_name)
            parent_item.setText(2, cert.crt_po_number or "")

            # Cert Date
            cert_date_str = ""
            if cert.crt_date:
                if hasattr(cert.crt_date, "strftime"):
                    cert_date_str = cert.crt_date.strftime("%m/%d/%y")
                else:
                    cert_date_str = str(cert.crt_date)[:10]
            parent_item.setText(3, cert_date_str)

            # Added Date
            added_date_str = ""
            if cert.crt_added_date:
                if hasattr(cert.crt_added_date, "strftime"):
                    added_date_str = cert.crt_added_date.strftime("%m/%d/%y")
                else:
                    added_date_str = str(cert.crt_added_date)[:10]
            parent_item.setText(4, added_date_str)

            # File count
            file_count = len(cert.media_files)
            parent_item.setText(5, str(file_count))

            # Store certification index for later retrieval
            parent_item.setData(0, Qt.ItemDataRole.UserRole, cert_idx)
            parent_item.setData(1, Qt.ItemDataRole.UserRole, "cert")

            # Enable tri-state checkbox for parent
            parent_item.setFlags(
                parent_item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsAutoTristate
            )
            parent_item.setCheckState(0, Qt.CheckState.Unchecked)

            # Check if certification is old and apply warning styling
            # Parse string dates (SQLite returns strings, SQL Server returns datetime)
            cert_date = cert.crt_date
            if isinstance(cert_date, str):
                try:
                    cert_date = datetime.fromisoformat(cert_date)
                except ValueError:
                    cert_date = None

            if warning_brush and cert_date:
                if cert_date < warning_cutoff:
                    for col in range(6):
                        parent_item.setForeground(col, warning_brush)
                    parent_item.setText(0, f"⚠ {cert.crt_cert_no}")
                    age_days = (datetime.now() - cert_date).days
                    parent_item.setToolTip(
                        0, f"Warning: This certification is {age_days} days old"
                    )

            # Add child items for each file
            for file_idx, media_file in enumerate(cert.media_files):
                child_item = QTreeWidgetItem()
                # Show filename and description on single line
                filename = Path(media_file.med_full_path).name
                desc = media_file.med_description
                if len(desc) > 40:
                    desc = desc[:40] + "..."
                child_item.setText(0, f"📄 {filename} ({desc})" if desc else f"📄 {filename}")
                # Clear description column for files (shown inline now)
                child_item.setText(1, "")

                # Store file index for later retrieval
                child_item.setData(0, Qt.ItemDataRole.UserRole, file_idx)
                child_item.setData(1, Qt.ItemDataRole.UserRole, "file")

                # Enable checkbox for child
                child_item.setFlags(child_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                child_item.setCheckState(0, Qt.CheckState.Unchecked)

                parent_item.addChild(child_item)

            self._tree.addTopLevelItem(parent_item)

        self.selection_changed.emit()

    def clear(self) -> None:
        """Clear the tree."""
        self._certifications = []
        self._tree.clear()
        self.selection_changed.emit()

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item checkbox state change."""
        if self._updating_checkboxes or column != 0:
            return

        self._updating_checkboxes = True
        try:
            item_type = item.data(1, Qt.ItemDataRole.UserRole)

            if item_type == "cert":
                # Parent checkbox changed - update all children
                check_state = item.checkState(0)
                if check_state != Qt.CheckState.PartiallyChecked:
                    for i in range(item.childCount()):
                        item.child(i).setCheckState(0, check_state)
            elif item_type == "file":
                # Child checkbox changed - update parent
                parent = item.parent()
                if parent:
                    self._update_parent_check_state(parent)

            self.selection_changed.emit()
        finally:
            self._updating_checkboxes = False

    def _update_parent_check_state(self, parent: QTreeWidgetItem) -> None:
        """Update parent checkbox based on children states."""
        checked_count = 0
        total_count = parent.childCount()

        for i in range(total_count):
            if parent.child(i).checkState(0) == Qt.CheckState.Checked:
                checked_count += 1

        if checked_count == 0:
            parent.setCheckState(0, Qt.CheckState.Unchecked)
        elif checked_count == total_count:
            parent.setCheckState(0, Qt.CheckState.Checked)
        else:
            parent.setCheckState(0, Qt.CheckState.PartiallyChecked)

    def _select_all(self) -> None:
        """Select all certifications and files."""
        self._updating_checkboxes = True
        try:
            for i in range(self._tree.topLevelItemCount()):
                parent = self._tree.topLevelItem(i)
                parent.setCheckState(0, Qt.CheckState.Checked)
                for j in range(parent.childCount()):
                    parent.child(j).setCheckState(0, Qt.CheckState.Checked)
            self.selection_changed.emit()
        finally:
            self._updating_checkboxes = False

    def _deselect_all(self) -> None:
        """Deselect all certifications and files."""
        self._updating_checkboxes = True
        try:
            for i in range(self._tree.topLevelItemCount()):
                parent = self._tree.topLevelItem(i)
                parent.setCheckState(0, Qt.CheckState.Unchecked)
                for j in range(parent.childCount()):
                    parent.child(j).setCheckState(0, Qt.CheckState.Unchecked)
            self.selection_changed.emit()
        finally:
            self._updating_checkboxes = False

    def get_selected_certifications(self) -> list[Certification]:
        """Get list of selected certifications with only selected files.

        Returns certifications that have at least one file selected,
        with media_files filtered to only include selected files.
        """
        selected = []

        for i in range(self._tree.topLevelItemCount()):
            parent = self._tree.topLevelItem(i)
            cert_idx = parent.data(0, Qt.ItemDataRole.UserRole)
            cert = self._certifications[cert_idx]

            # Collect selected files
            selected_files: list[MediaFile] = []
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.CheckState.Checked:
                    file_idx = child.data(0, Qt.ItemDataRole.UserRole)
                    selected_files.append(cert.media_files[file_idx])

            # Only include cert if at least one file is selected
            if selected_files:
                # Create a copy of the certification with only selected files
                cert_copy = replace(cert, media_files=selected_files)
                selected.append(cert_copy)

        return selected

    def get_selected_count(self) -> int:
        """Get count of selected certifications (with at least one file selected)."""
        return len(self.get_selected_certifications())

    def get_total_file_count(self) -> int:
        """Get total file count for selected files."""
        return sum(len(c.media_files) for c in self.get_selected_certifications())

    def select_single(self) -> None:
        """Select first certification and all its files if only one exists."""
        if len(self._certifications) == 1 and self._tree.topLevelItemCount() == 1:
            parent = self._tree.topLevelItem(0)
            self._updating_checkboxes = True
            try:
                parent.setCheckState(0, Qt.CheckState.Checked)
                for i in range(parent.childCount()):
                    parent.child(i).setCheckState(0, Qt.CheckState.Checked)
                self.selection_changed.emit()
            finally:
                self._updating_checkboxes = False

    def _restore_column_widths(self) -> None:
        """Restore column widths from settings or use defaults."""
        settings = load_settings()
        widths = settings.cert_table_column_widths

        if widths and len(widths) >= 6:
            for i, width in enumerate(widths[:6]):
                self._tree.setColumnWidth(i, width)
        else:
            # Default widths
            self._tree.setColumnWidth(0, 140)
            self._tree.setColumnWidth(1, 200)  # Customer
            self._tree.setColumnWidth(2, 100)
            self._tree.setColumnWidth(3, 90)
            self._tree.setColumnWidth(4, 90)
            self._tree.setColumnWidth(5, 50)

    def _on_column_resized(self, index: int, old_size: int, new_size: int) -> None:
        """Save column widths when user resizes."""
        # Collect current widths
        widths = [self._tree.columnWidth(i) for i in range(6)]

        # Save to settings
        settings = load_settings()
        settings.cert_table_column_widths = widths
        save_settings(settings)
