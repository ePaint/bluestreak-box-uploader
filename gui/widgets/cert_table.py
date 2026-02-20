"""Certification table with checkboxes and modern styling."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QCheckBox,
    QAbstractItemView,
)

from database.models import Certification
from gui.theme import COLORS, SPACING


class CertificationTable(QWidget):
    """Table widget displaying certifications with selection checkboxes."""

    selection_changed = Signal()  # Emitted when selection changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self._certifications: list[Certification] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["", "Cert No", "Customer", "PO#", "Files"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        # Column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Cert No
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Customer
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # PO#
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Files
        self._table.setColumnWidth(0, 40)
        self._table.setColumnWidth(4, 60)

        # Row height
        self._table.verticalHeader().setDefaultSectionSize(42)

        layout.addWidget(self._table)

        # Buttons row
        self._btn_layout = QHBoxLayout()
        self._btn_layout.setSpacing(SPACING["sm"])

        self._select_all_btn = QPushButton("Select All")
        self._select_all_btn.clicked.connect(self._select_all)
        self._btn_layout.addWidget(self._select_all_btn)

        self._deselect_all_btn = QPushButton("Clear")
        self._deselect_all_btn.clicked.connect(self._deselect_all)
        self._btn_layout.addWidget(self._deselect_all_btn)

        self._btn_layout.addStretch()

        layout.addLayout(self._btn_layout)

    def add_toolbar_widget(self, widget: QWidget) -> None:
        """Add a widget to the toolbar row (after the stretch)."""
        self._btn_layout.addWidget(widget)

    def set_certifications(self, certifications: list[Certification]) -> None:
        """Set the certifications to display."""
        self._certifications = certifications
        self._table.setRowCount(len(certifications))

        for row, cert in enumerate(certifications):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self._on_checkbox_changed)
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self._table.setCellWidget(row, 0, checkbox_widget)

            # Cert No
            cert_item = QTableWidgetItem(cert.crt_cert_no)
            cert_item.setFlags(cert_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 1, cert_item)

            # Customer
            cust_item = QTableWidgetItem(cert.crt_cust_name)
            cust_item.setFlags(cust_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 2, cust_item)

            # PO#
            po_item = QTableWidgetItem(cert.crt_po_number or "")
            po_item.setFlags(po_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 3, po_item)

            # File count
            file_count = len(cert.media_files)
            files_item = QTableWidgetItem(str(file_count))
            files_item.setFlags(files_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            files_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 4, files_item)

        self.selection_changed.emit()

    def clear(self) -> None:
        """Clear the table."""
        self._certifications = []
        self._table.setRowCount(0)
        self.selection_changed.emit()

    def _get_checkbox(self, row: int) -> QCheckBox | None:
        """Get the checkbox for a row."""
        widget = self._table.cellWidget(row, 0)
        if widget:
            return widget.findChild(QCheckBox)
        return None

    def _on_checkbox_changed(self) -> None:
        """Handle checkbox state change."""
        self.selection_changed.emit()

    def _select_all(self) -> None:
        """Select all certifications."""
        for row in range(self._table.rowCount()):
            checkbox = self._get_checkbox(row)
            if checkbox:
                checkbox.setChecked(True)

    def _deselect_all(self) -> None:
        """Deselect all certifications."""
        for row in range(self._table.rowCount()):
            checkbox = self._get_checkbox(row)
            if checkbox:
                checkbox.setChecked(False)

    def get_selected_certifications(self) -> list[Certification]:
        """Get list of selected certifications."""
        selected = []
        for row in range(self._table.rowCount()):
            checkbox = self._get_checkbox(row)
            if checkbox and checkbox.isChecked():
                selected.append(self._certifications[row])
        return selected

    def get_selected_count(self) -> int:
        """Get count of selected certifications."""
        return len(self.get_selected_certifications())

    def get_total_file_count(self) -> int:
        """Get total file count for selected certifications."""
        return sum(len(c.media_files) for c in self.get_selected_certifications())

    def select_single(self) -> None:
        """Select first certification if only one exists."""
        if len(self._certifications) == 1:
            checkbox = self._get_checkbox(0)
            if checkbox:
                checkbox.setChecked(True)
