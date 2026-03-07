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
from gui.theme import COLORS, SPACING, SIZES


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
        self._search_input.setPlaceholderText("Search by order, cert, filename...")
        self._search_input.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(self._search_input, stretch=1)

        self._status_filter = QComboBox()
        self._status_filter.addItems(["All", "Success", "Failed"])
        self._status_filter.setFixedWidth(SIZES["filter_w"])
        self._status_filter.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self._status_filter)

        self._export_btn = QPushButton("Export CSV")
        self._export_btn.setFixedWidth(SIZES["filter_w"])
        self._export_btn.clicked.connect(self._export_all)
        toolbar.addWidget(self._export_btn)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setFixedWidth(SIZES["btn_w_xs"] - 10)
        self._refresh_btn.clicked.connect(self._load_history)
        toolbar.addWidget(self._refresh_btn)

        layout.addLayout(toolbar)

        # Tree widget for grouped display
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Time", "Order", "Cert", "Filename", "Status", "Error"])
        self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)

        # Column widths
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

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
        self._display_records(records)

    def _display_records(self, records: list[UploadHistoryRecord]) -> None:
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

        for record_date in sorted_dates:
            date_records = grouped[record_date]

            # Create date group item
            date_str = record_date.strftime("%A, %B %d, %Y")
            success_count = sum(1 for r in date_records if r.status == "success")
            fail_count = sum(1 for r in date_records if r.status == "failed")
            summary = f"{len(date_records)} uploads"
            if fail_count > 0:
                summary += f" ({fail_count} failed)"

            date_item = QTreeWidgetItem([date_str, "", "", summary, "", ""])
            date_item.setFirstColumnSpanned(False)
            date_item.setExpanded(True)
            date_item.setData(0, Qt.ItemDataRole.UserRole, None)  # No session for date group

            # Style the date header
            font = date_item.font(0)
            font.setBold(True)
            date_item.setFont(0, font)
            date_item.setForeground(0, QColor(COLORS["accent"]))

            self._tree.addTopLevelItem(date_item)

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
                    session_summary,
                    "",
                    first.customer_name or "",
                ])
                session_item.setData(0, Qt.ItemDataRole.UserRole, session_id)
                session_item.setExpanded(False)

                date_item.addChild(session_item)

                # Add individual records
                for record in session_records:
                    time_str = record.timestamp.strftime("%H:%M:%S") if record.timestamp else ""
                    status_icon = "\u2713" if record.status == "success" else "\u2717"

                    record_item = QTreeWidgetItem([
                        time_str,
                        str(record.order_id),
                        record.cert_no,
                        record.filename,
                        status_icon,
                        record.error_msg or "",
                    ])

                    # Color status
                    if record.status == "success":
                        record_item.setForeground(4, QColor(COLORS["success"]))
                    else:
                        record_item.setForeground(4, QColor(COLORS["error"]))
                        record_item.setForeground(5, QColor(COLORS["error"]))

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
