"""Upload history viewer widget with search and filtering."""

from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QFileDialog,
    QMenu,
    QMessageBox,
    QHeaderView,
)

from database.history import (
    search_history,
    get_session_records,
    export_history_to_csv,
)
from database.models import UploadHistoryRecord
from gui.theme import COLORS, FONT_SIZE, SPACING, SIZES
from settings import load_settings, save_settings


class HistoryViewer(QWidget):
    """Widget for viewing and searching upload history."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
        self._setup_ui()
        self._load_history()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(SPACING["sm"])

        self._search_input = QLineEdit()
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setPlaceholderText("Search by order, cert, filename...")
        self._search_input.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self._search_input, stretch=1)

        self._status_filter = QComboBox()
        self._status_filter.addItems(["All", "Success", "Failed"])
        self._status_filter.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self._status_filter)

        self._export_btn = QPushButton("Export CSV")
        self._export_btn.clicked.connect(self._export_all)
        toolbar.addWidget(self._export_btn)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._load_history)
        toolbar.addWidget(self._refresh_btn)

        self._clear_btn = QPushButton("Clear...")
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        toolbar.addWidget(self._clear_btn)

        layout.addLayout(toolbar)

        # Tree widget for grouped display
        self._tree = QTreeWidget()
        self._tree.setObjectName("historyTree")  # For denser row styling
        self._tree.setHeaderLabels(["Time", "Order", "Cert", "Customer", "PO#", "Filename", "Status", "Error"])
        self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)

        # Column widths - all interactive for user resizing
        header = self._tree.header()
        # Set header font size programmatically (stylesheet may not apply on Windows)
        header_font = header.font()
        header_font.setPointSize(FONT_SIZE["sm"])
        header.setFont(header_font)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Order
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Cert
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Customer
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # PO#
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Filename
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)  # Status
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)  # Error

        # Restore saved widths
        self._restore_column_widths()

        # Save on resize
        header.sectionResized.connect(self._on_column_resized)

        layout.addWidget(self._tree)

    def _on_search_changed(self, text: str) -> None:
        """Debounce search input."""
        self._search_timer.start(300)

    def _on_filter_changed(self, text: str) -> None:
        """Trigger search when filter changes."""
        self._load_history()

    def _do_search(self) -> None:
        """Execute search after debounce."""
        self._load_history()

    def _load_history(self) -> None:
        """Load and display history records."""
        query = self._search_input.text().strip()
        status_text = self._status_filter.currentText()
        status = status_text.lower() if status_text != "All" else None

        records = search_history(query=query, status=status, limit=500)
        self._display_records(records, is_searching=bool(query))

    def _display_records(self, records: list[UploadHistoryRecord], is_searching: bool = False) -> None:
        """Display records grouped by date."""
        self._tree.clear()

        if not records:
            empty_item = QTreeWidgetItem(["No upload history yet"])
            empty_item.setForeground(0, QColor(COLORS["text_secondary"]))
            self._tree.addTopLevelItem(empty_item)
            return

        # Group by date
        grouped: dict[date, list[UploadHistoryRecord]] = {}
        for record in records:
            if record.timestamp:
                record_date = record.timestamp.date()
                if record_date not in grouped:
                    grouped[record_date] = []
                grouped[record_date].append(record)

        # Sort dates newest first
        sorted_dates = sorted(grouped.keys(), reverse=True)

        for idx, record_date in enumerate(sorted_dates):
            date_records = grouped[record_date]

            # Create date group item
            date_str = record_date.strftime("%A, %B %d, %Y")
            success_count = sum(1 for r in date_records if r.status == "success")
            fail_count = sum(1 for r in date_records if r.status == "failed")
            summary = f"{len(date_records)} uploads"
            if fail_count > 0:
                summary += f" ({fail_count} failed)"

            date_item = QTreeWidgetItem([date_str, "", "", "", "", summary, "", ""])
            date_item.setFirstColumnSpanned(False)
            date_item.setData(0, Qt.ItemDataRole.UserRole, None)  # No session for date group

            # Style the date header
            font = date_item.font(0)
            font.setBold(True)
            date_item.setFont(0, font)
            date_item.setForeground(0, QColor(COLORS["accent"]))

            self._tree.addTopLevelItem(date_item)
            # Expand all when searching, only most recent when not searching
            date_item.setExpanded(is_searching or idx == 0)

            # Group by session within date
            sessions: dict[str, list[UploadHistoryRecord]] = {}
            for record in date_records:
                if record.session_id not in sessions:
                    sessions[record.session_id] = []
                sessions[record.session_id].append(record)

            for session_id, session_records in sessions.items():
                # Create session group
                first = session_records[0]
                session_time = first.timestamp.strftime("%H:%M") if first.timestamp else ""
                session_success = sum(1 for r in session_records if r.status == "success")
                session_fail = sum(1 for r in session_records if r.status == "failed")
                session_summary = f"{len(session_records)} files"
                if session_fail > 0:
                    session_summary += f" ({session_fail} failed)"

                session_item = QTreeWidgetItem([
                    session_time,
                    str(first.order_id),
                    "",
                    first.customer_name or "",
                    "",
                    session_summary,
                    "",
                    "",
                ])
                session_item.setData(0, Qt.ItemDataRole.UserRole, session_id)
                session_item.setExpanded(is_searching)

                date_item.addChild(session_item)

                # Add individual records
                for record in session_records:
                    time_str = record.timestamp.strftime("%H:%M:%S") if record.timestamp else ""
                    status_icon = "\u2713" if record.status == "success" else "\u2717"

                    record_item = QTreeWidgetItem([
                        time_str,
                        str(record.order_id),
                        record.cert_no,
                        record.customer_name or "",
                        record.po_number or "",
                        record.filename,
                        status_icon,
                        record.error_msg or "",
                    ])

                    # Color status
                    if record.status == "success":
                        record_item.setForeground(6, QColor(COLORS["success"]))
                    else:
                        record_item.setForeground(6, QColor(COLORS["error"]))
                        record_item.setForeground(7, QColor(COLORS["error"]))

                    record_item.setData(0, Qt.ItemDataRole.UserRole, session_id)
                    session_item.addChild(record_item)

    def _show_context_menu(self, position) -> None:
        """Show context menu for export options."""
        item = self._tree.itemAt(position)
        if not item:
            return

        session_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not session_id:
            return

        menu = QMenu(self)
        export_session = menu.addAction("Export this session to CSV...")
        action = menu.exec(self._tree.mapToGlobal(position))

        if action == export_session:
            self._export_session(session_id)

    def _export_session(self, session_id: str) -> None:
        """Export a single session to CSV."""
        records = get_session_records(session_id)
        if not records:
            QMessageBox.warning(self, "Export", "No records found for this session.")
            return

        self._do_export(records, f"session_{session_id[:8]}")

    def _export_all(self) -> None:
        """Export all visible records to CSV."""
        query = self._search_input.text().strip()
        status_text = self._status_filter.currentText()
        status = status_text.lower() if status_text != "All" else None

        records = search_history(query=query, status=status, limit=10000)
        if not records:
            QMessageBox.warning(self, "Export", "No records to export.")
            return

        self._do_export(records, "upload_history")

    def _do_export(self, records: list[UploadHistoryRecord], default_name: str) -> None:
        """Common export logic."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            f"{default_name}.csv",
            "CSV Files (*.csv)",
        )

        if filepath:
            try:
                export_history_to_csv(records, Path(filepath))
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Exported {len(records)} records to {filepath}",
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")

    def refresh(self) -> None:
        """Public method to refresh history display."""
        self._load_history()

    def _on_clear_clicked(self) -> None:
        """Show clear history dialog."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Clear all upload history?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from database.history import clear_all_history

            count = clear_all_history()
            self.refresh()

    def _restore_column_widths(self) -> None:
        """Restore column widths from settings or use defaults."""
        settings = load_settings()
        widths = settings.history_table_column_widths

        if widths and len(widths) >= 8:
            for i, width in enumerate(widths[:8]):
                self._tree.setColumnWidth(i, int(width))
        else:
            self._tree.setColumnWidth(0, SIZES["hist_col_time"])
            self._tree.setColumnWidth(1, SIZES["hist_col_order"])
            self._tree.setColumnWidth(2, SIZES["hist_col_cert"])
            self._tree.setColumnWidth(3, SIZES["hist_col_customer"])
            self._tree.setColumnWidth(4, SIZES["hist_col_po"])
            self._tree.setColumnWidth(5, SIZES["hist_col_filename"])
            self._tree.setColumnWidth(6, SIZES["hist_col_status"])
            self._tree.setColumnWidth(7, SIZES["hist_col_error"])

    def _on_column_resized(self, index: int, old_size: int, new_size: int) -> None:
        """Save column widths when user resizes."""
        # Explicit int() to avoid Shiboken type issues
        widths = [int(self._tree.columnWidth(i)) for i in range(8)]
        settings = load_settings()
        settings.history_table_column_widths = widths
        save_settings(settings)
