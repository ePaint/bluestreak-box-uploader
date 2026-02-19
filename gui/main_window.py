"""Main application window."""

from pathlib import Path

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QMessageBox,
    QGroupBox,
)

from database.models import Certification, Customer
from settings import load_settings, save_settings
from settings.config import get_database_config
from gui.widgets import CertificationTable, LogViewer, UploadProgressWidget
from gui.settings_dialog import SettingsDialog
from gui.workers import QueryWorker, UploadWorker


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bluestreak Box Uploader")
        self.setMinimumSize(800, 700)

        self._certifications: list[Certification] = []
        self._customer: Customer | None = None
        self._query_worker: QueryWorker | None = None
        self._upload_worker: UploadWorker | None = None

        self._setup_menu()
        self._setup_ui()
        self._load_last_order()
        self._update_ui_state()

    def _setup_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        settings_action = QAction("Settings...", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Order Lookup group
        lookup_group = QGroupBox("Order Lookup")
        lookup_layout = QHBoxLayout(lookup_group)

        lookup_layout.addWidget(QLabel("Order ID:"))

        self._order_input = QLineEdit()
        self._order_input.setPlaceholderText("Enter order ID (e.g., 444337)")
        self._order_input.returnPressed.connect(self._search_order)
        lookup_layout.addWidget(self._order_input)

        self._search_btn = QPushButton("Search")
        self._search_btn.clicked.connect(self._search_order)
        lookup_layout.addWidget(self._search_btn)

        layout.addWidget(lookup_group)

        # Certifications group
        certs_group = QGroupBox("Certifications Found")
        certs_layout = QVBoxLayout(certs_group)

        self._cert_table = CertificationTable()
        self._cert_table.selection_changed.connect(self._update_ui_state)
        certs_layout.addWidget(self._cert_table)

        # Auto-upload checkbox
        options_layout = QHBoxLayout()
        self._auto_upload_checkbox = QCheckBox("Auto-upload when single certification found")
        settings = load_settings()
        self._auto_upload_checkbox.setChecked(settings.get("auto_upload_single", True))
        self._auto_upload_checkbox.toggled.connect(self._on_auto_upload_changed)
        options_layout.addWidget(self._auto_upload_checkbox)
        options_layout.addStretch()
        certs_layout.addLayout(options_layout)

        # Warning label (hidden by default)
        self._warning_label = QLabel()
        self._warning_label.setStyleSheet("""
            QLabel {
                color: #ffd43b;
                background-color: #3d3d00;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        self._warning_label.setVisible(False)
        certs_layout.addWidget(self._warning_label)

        layout.addWidget(certs_group)

        # Upload Progress group
        progress_group = QGroupBox("Upload Progress")
        progress_layout = QVBoxLayout(progress_group)

        self._progress_widget = UploadProgressWidget()
        progress_layout.addWidget(self._progress_widget)

        layout.addWidget(progress_group)

        # Log group
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)

        self._log = LogViewer()
        self._log.setMinimumHeight(150)
        log_layout.addWidget(self._log)

        layout.addWidget(log_group)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._upload_btn = QPushButton("Upload Selected")
        self._upload_btn.setMinimumWidth(120)
        self._upload_btn.clicked.connect(self._start_upload)
        button_layout.addWidget(self._upload_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setMinimumWidth(100)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel_upload)
        button_layout.addWidget(self._cancel_btn)

        layout.addLayout(button_layout)

    def _load_last_order(self) -> None:
        """Load the last searched order ID."""
        settings = load_settings()
        last_order = settings.get("last_order_id", "")
        if last_order:
            self._order_input.setText(last_order)

    def _update_ui_state(self) -> None:
        """Update button states based on current selection."""
        has_selection = self._cert_table.get_selected_count() > 0
        has_box_mapping = self._customer is not None and self._customer.cst_integration_id is not None
        is_processing = (
            (self._query_worker is not None and self._query_worker.isRunning())
            or (self._upload_worker is not None and self._upload_worker.isRunning())
        )

        self._upload_btn.setEnabled(has_selection and has_box_mapping and not is_processing)
        self._cancel_btn.setEnabled(is_processing)
        self._search_btn.setEnabled(not is_processing)
        self._order_input.setEnabled(not is_processing)

        # Update warning visibility
        if self._customer is not None and self._customer.cst_integration_id is None:
            self._warning_label.setText(
                f"Warning: Customer '{self._customer.cst_name}' is not mapped to a Box folder. "
                "Set cstIntegrationID in the database to enable uploads."
            )
            self._warning_label.setVisible(True)
        else:
            self._warning_label.setVisible(False)

    def _show_settings(self) -> None:
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()

    def _on_auto_upload_changed(self, checked: bool) -> None:
        """Save auto-upload preference."""
        settings = load_settings()
        settings["auto_upload_single"] = checked
        save_settings(settings)

    def _search_order(self) -> None:
        """Search for certifications by order ID."""
        order_text = self._order_input.text().strip()
        if not order_text:
            QMessageBox.warning(self, "Input Required", "Please enter an Order ID.")
            return

        try:
            order_id = int(order_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Order ID must be a number.")
            return

        # Save last order
        settings = load_settings()
        settings["last_order_id"] = order_text
        save_settings(settings)

        # Clear previous results
        self._cert_table.clear()
        self._certifications = []
        self._customer = None
        self._progress_widget.reset()
        self._log.clear()
        self._log.log(f"Searching for order {order_id}...")

        # Start query
        config = get_database_config()
        self._query_worker = QueryWorker(config, order_id)
        self._query_worker.finished.connect(self._on_query_finished)
        self._query_worker.error.connect(self._on_query_error)
        self._query_worker.start()

        self._update_ui_state()

    def _on_query_finished(self, certs: list[Certification], customer: Customer | None) -> None:
        """Handle query completion."""
        self._certifications = certs
        self._customer = customer
        self._query_worker = None

        if not certs:
            self._log.log_warning("No certifications found for this order.")
            self._update_ui_state()
            return

        self._cert_table.set_certifications(certs)

        # Log results
        total_files = sum(len(c.media_files) for c in certs)
        self._log.log_success(f"Found {len(certs)} certification(s) with {total_files} file(s)")

        if customer:
            self._log.log(f"Customer: {customer.cst_name}", timestamp=False)
            if customer.cst_integration_id:
                self._log.log(f"Box Folder ID: {customer.cst_integration_id}", timestamp=False)
            else:
                self._log.log_warning("Customer not mapped to Box folder")

        # Auto-upload if single cert and setting enabled
        if (
            len(certs) == 1
            and self._auto_upload_checkbox.isChecked()
            and customer
            and customer.cst_integration_id
        ):
            self._cert_table.select_single()
            self._log.log("Auto-uploading single certification...")
            self._start_upload()
        else:
            self._update_ui_state()

    def _on_query_error(self, message: str) -> None:
        """Handle query error."""
        self._query_worker = None
        self._log.log_error(message)
        self._update_ui_state()

    def _start_upload(self) -> None:
        """Start uploading selected certifications."""
        selected = self._cert_table.get_selected_certifications()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select certifications to upload.")
            return

        if self._customer is None or self._customer.cst_integration_id is None:
            QMessageBox.warning(
                self,
                "Box Folder Not Configured",
                "The customer is not mapped to a Box folder.\n"
                "Please set cstIntegrationID in the database.",
            )
            return

        settings = load_settings()
        jwt_path = settings.get("box_jwt_config_path", "")
        if not jwt_path:
            result = QMessageBox.question(
                self,
                "Box Not Configured",
                "Box.com is not configured. Would you like to open settings?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if result == QMessageBox.StandardButton.Yes:
                self._show_settings()
            return

        media_base = settings.get("media_base_path", "")
        if not media_base:
            result = QMessageBox.question(
                self,
                "Media Path Not Configured",
                "Media base path is not configured. Would you like to open settings?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if result == QMessageBox.StandardButton.Yes:
                self._show_settings()
            return

        # Calculate totals
        total_files = sum(len(c.media_files) for c in selected)
        self._progress_widget.set_total(total_files)
        self._log.log(f"Starting upload of {total_files} file(s) from {len(selected)} certification(s)...")

        # Start upload worker
        self._upload_worker = UploadWorker(
            jwt_config_path=jwt_path,
            certifications=selected,
            root_folder_id=self._customer.cst_integration_id,
            media_base_path=Path(media_base),
        )
        self._upload_worker.progress.connect(self._on_upload_progress)
        self._upload_worker.file_completed.connect(self._on_file_completed)
        self._upload_worker.finished.connect(self._on_upload_finished)
        self._upload_worker.error.connect(self._on_upload_error)
        self._upload_worker.start()

        self._update_ui_state()

    def _cancel_upload(self) -> None:
        """Cancel current upload."""
        if self._upload_worker and self._upload_worker.isRunning():
            self._upload_worker.cancel()
            self._log.log_warning("Upload cancelled")

    def _on_upload_progress(self, current: int, total: int, filename: str) -> None:
        """Handle upload progress update."""
        self._progress_widget.update_progress(current, total, filename)

    def _on_file_completed(self, job) -> None:
        """Handle individual file completion."""
        filename = Path(job.media_file.med_full_path).name
        if job.status.value == "completed":
            self._log.log_success(f"Uploaded: {filename}")
        else:
            self._log.log_error(f"Failed: {filename} - {job.error_message}")

    def _on_upload_finished(self, success_count: int, failed_count: int) -> None:
        """Handle upload completion."""
        self._upload_worker = None
        total = success_count + failed_count
        self._progress_widget.set_completed(success_count, total)

        self._log.log("", timestamp=False)
        self._log.log("=== Upload Complete ===", timestamp=False)
        self._log.log(f"Successful: {success_count}", timestamp=False)
        self._log.log(f"Failed: {failed_count}", timestamp=False)

        self._update_ui_state()

        QMessageBox.information(
            self,
            "Upload Complete",
            f"Successfully uploaded {success_count} of {total} files.",
        )

    def _on_upload_error(self, message: str) -> None:
        """Handle upload error."""
        self._upload_worker = None
        self._log.log_error(message)
        self._progress_widget.set_error(message)
        self._update_ui_state()
