"""Settings dialog with modern styling and three tabs: Database, Box.com, Paths."""

from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QSlider,
    QComboBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QLabel,
    QDialogButtonBox,
    QDateEdit,
    QCheckBox,
)

from PySide6.QtWidgets import QApplication

from settings import load_settings, save_settings
from database.connection import DatabaseConfig, check_connection
from gui.theme import SPACING, SIZES, COLORS, get_icon


class SettingsDialog(QDialog):
    """Settings dialog with Database, Box, and Paths tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(SIZES["dialog_min_w"])
        self.setMinimumHeight(SIZES["dialog_min_h"])
        # Pre-cache info icon pixmap to avoid delay during UI setup
        self._info_pixmap = get_icon("info", COLORS["text_secondary"]).pixmap(16, 16)
        self._setup_ui()
        self._load_settings()

    def showEvent(self, event) -> None:
        """Match calendar popup width to date edit width after layout is done."""
        super().showEvent(event)
        calendar = self._cert_warning_date.calendarWidget()
        calendar.setMinimumWidth(self._cert_warning_date.width())

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        # Tab widget
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # General tab (first)
        self._general_tab = QWidget()
        self._setup_general_tab()
        self._tabs.addTab(self._general_tab, get_icon("settings"), "General")

        # Database tab
        self._db_tab = QWidget()
        self._setup_db_tab()
        self._tabs.addTab(self._db_tab, get_icon("database"), "Database")

        # Box tab
        self._box_tab = QWidget()
        self._setup_box_tab()
        self._tabs.addTab(self._box_tab, get_icon("box"), "Box.com")

        # Paths tab
        self._paths_tab = QWidget()
        self._setup_paths_tab()
        self._tabs.addTab(self._paths_tab, get_icon("folder"), "Paths")

        # Button box
        button_box = QDialogButtonBox()

        self._save_btn = QPushButton("Save")
        self._save_btn.setProperty("primary", True)
        self._save_btn.clicked.connect(self._save_and_close)
        button_box.addButton(self._save_btn, QDialogButtonBox.ButtonRole.AcceptRole)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)
        button_box.addButton(self._cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)

        layout.addWidget(button_box)

    def _create_info_icon(self, tooltip: str) -> QLabel:
        """Create a small info icon with tooltip."""
        label = QLabel()
        label.setPixmap(self._info_pixmap)
        label.setToolTip(tooltip)
        label.setCursor(Qt.CursorShape.WhatsThisCursor)
        return label

    def _create_label_with_info(self, text: str, tooltip: str) -> QWidget:
        """Create a label with an info icon next to it."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(QLabel(text))
        layout.addWidget(self._create_info_icon(tooltip))
        layout.addStretch()
        return container

    def _setup_general_tab(self) -> None:
        layout = QFormLayout(self._general_tab)
        layout.setSpacing(SPACING["sm"])
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])

        # Theme selection
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["dark", "light"])
        self._theme_combo.setMinimumWidth(SIZES["filter_w"])
        layout.addRow(
            self._create_label_with_info("Theme:", "Application color theme. Requires restart to take effect."),
            self._theme_combo
        )

        # Font size slider
        font_size_layout = QHBoxLayout()
        font_size_layout.setSpacing(SPACING["sm"])

        self._font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self._font_size_slider.setRange(8, 16)
        self._font_size_slider.setValue(10)
        self._font_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._font_size_slider.setTickInterval(1)
        self._font_size_slider.valueChanged.connect(self._on_font_size_changed)
        font_size_layout.addWidget(self._font_size_slider)

        self._font_size_label = QLabel("10 pt")
        self._font_size_label.setMinimumWidth(60)  # Fits "16 pt" at larger font sizes
        font_size_layout.addWidget(self._font_size_label)

        layout.addRow(
            self._create_label_with_info("Font Size:", "Base font size for all text. Requires restart to take effect."),
            font_size_layout
        )

        # UI Scale dropdown
        self._scale_combo = QComboBox()
        self._scale_combo.addItems(["100%", "125%", "150%"])
        self._scale_combo.setMinimumWidth(SIZES["filter_w"])
        layout.addRow(
            self._create_label_with_info("UI Scale:", "Scale all UI elements (100%, 125%, 150%). Requires restart to take effect."),
            self._scale_combo
        )

        # Cert date warning (mandatory - uploads blocked until set)
        cert_date_layout = QHBoxLayout()
        cert_date_layout.setSpacing(SPACING["sm"])
        self._cert_warning_date = QDateEdit()
        self._cert_warning_date.setCalendarPopup(True)
        self._cert_warning_date.setDisplayFormat("MM/dd/yyyy")
        self._cert_warning_date.setMinimumDate(QDate(2020, 1, 1))
        self._cert_warning_date.setMaximumDate(QDate.currentDate())
        self._cert_warning_date.dateChanged.connect(self._on_cert_warning_date_changed)
        cert_date_layout.addWidget(self._cert_warning_date)

        self._cert_warning_clear = QPushButton("Unset")
        self._cert_warning_clear.clicked.connect(self._toggle_cert_warning_date)
        cert_date_layout.addWidget(self._cert_warning_clear)

        layout.addRow(
            self._create_label_with_info(
                "Cert Warning Date:",
                "Certs created before this date will show a warning before upload. "
                "Set to date when digital signing was implemented."
            ),
            cert_date_layout
        )

        # Account status checks
        credit_hold_container = QWidget()
        credit_hold_layout = QHBoxLayout(credit_hold_container)
        credit_hold_layout.setContentsMargins(0, 0, 0, 0)
        credit_hold_layout.setSpacing(4)
        self._check_credit_hold = QCheckBox("Enable Credit Hold Warning")
        credit_hold_layout.addWidget(self._check_credit_hold)
        credit_hold_layout.addWidget(self._create_info_icon(
            "Show warning before uploading if customer has credit hold status."
        ))
        credit_hold_layout.addStretch()
        layout.addRow("Account Checks:", credit_hold_container)

        cod_terms_container = QWidget()
        cod_terms_layout = QHBoxLayout(cod_terms_container)
        cod_terms_layout.setContentsMargins(0, 0, 0, 0)
        cod_terms_layout.setSpacing(4)
        self._check_cod_terms = QCheckBox("Enable COD Payment Terms Warning")
        cod_terms_layout.addWidget(self._check_cod_terms)
        cod_terms_layout.addWidget(self._create_info_icon(
            "Show warning before uploading if customer has COD payment terms."
        ))
        cod_terms_layout.addStretch()
        layout.addRow("", cod_terms_container)

        # History retention
        self._history_retention = QComboBox()
        self._history_retention.addItems(["Keep forever", "30 days", "90 days", "1 year"])
        layout.addRow(
            self._create_label_with_info("History Retention:", "How long to keep upload history. Old records are cleaned on startup."),
            self._history_retention
        )

    def _setup_db_tab(self) -> None:
        layout = QFormLayout(self._db_tab)
        layout.setSpacing(SPACING["sm"])
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])

        # Driver selection
        self._db_driver = QComboBox()
        self._db_driver.addItems(["sqlserver", "sqlite"])
        self._db_driver.currentTextChanged.connect(self._on_driver_changed)
        layout.addRow(
            self._create_label_with_info("Driver:", "Database driver: SQL Server for production, SQLite for testing."),
            self._db_driver
        )

        # SQL Server fields
        self._db_host = QLineEdit()
        self._db_host.setPlaceholderText("e.g., 192.168.1.100")
        layout.addRow(
            self._create_label_with_info("Host:", "SQL Server hostname or IP address."),
            self._db_host
        )

        self._db_port = QSpinBox()
        self._db_port.setRange(1, 65535)
        self._db_port.setValue(1433)
        layout.addRow(
            self._create_label_with_info("Port:", "SQL Server port (default: 1433)."),
            self._db_port
        )

        self._db_database = QLineEdit()
        self._db_database.setText("Bluestreak")
        layout.addRow(
            self._create_label_with_info("Database:", "Database name on the SQL Server."),
            self._db_database
        )

        self._db_username = QLineEdit()
        layout.addRow(
            self._create_label_with_info("Username:", "SQL Server login username."),
            self._db_username
        )

        self._db_password = QLineEdit()
        self._db_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow(
            self._create_label_with_info("Password:", "SQL Server login password."),
            self._db_password
        )

        # SQLite path (for testing)
        sqlite_layout = QHBoxLayout()
        sqlite_layout.setSpacing(SPACING["sm"])
        self._db_sqlite_path = QLineEdit()
        self._db_sqlite_path.setPlaceholderText("Path to SQLite database")
        sqlite_layout.addWidget(self._db_sqlite_path)
        self._db_sqlite_browse = QPushButton("Browse...")
        self._db_sqlite_browse.clicked.connect(self._browse_sqlite)
        sqlite_layout.addWidget(self._db_sqlite_browse)
        layout.addRow(
            self._create_label_with_info("SQLite Path:", "Path to SQLite database file (for testing)."),
            sqlite_layout
        )

        # Test button
        self._db_test_btn = QPushButton("Test Connection")
        self._db_test_btn.setIcon(get_icon("plug"))
        self._db_test_btn.clicked.connect(self._test_db_connection)
        layout.addRow("", self._db_test_btn)

        # Search result limit
        self._search_limit = QSpinBox()
        self._search_limit.setRange(10, 1000)
        self._search_limit.setValue(100)
        self._search_limit.setSuffix(" orders")
        layout.addRow(
            self._create_label_with_info("Search Result Limit:", "Maximum number of orders returned when searching by partial order ID."),
            self._search_limit
        )

    def _setup_box_tab(self) -> None:
        layout = QFormLayout(self._box_tab)
        layout.setSpacing(SPACING["sm"])
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])

        # JWT config path
        jwt_layout = QHBoxLayout()
        jwt_layout.setSpacing(SPACING["sm"])
        self._box_jwt_path = QLineEdit()
        self._box_jwt_path.setPlaceholderText("Path to Box JWT config JSON file")
        jwt_layout.addWidget(self._box_jwt_path)
        self._box_jwt_browse = QPushButton("Browse...")
        self._box_jwt_browse.clicked.connect(self._browse_jwt)
        jwt_layout.addWidget(self._box_jwt_browse)
        layout.addRow(
            self._create_label_with_info(
                "JWT Config:",
                "Box JWT config JSON file. Download from Box Developer Console > "
                "Your App > Configuration > Generate a Public/Private Keypair."
            ),
            jwt_layout
        )

        # Test button
        self._box_test_btn = QPushButton("Test Connection")
        self._box_test_btn.setIcon(get_icon("plug"))
        self._box_test_btn.clicked.connect(self._test_box_connection)
        layout.addRow("", self._box_test_btn)

    def _setup_paths_tab(self) -> None:
        layout = QFormLayout(self._paths_tab)
        layout.setSpacing(SPACING["sm"])
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])

        # Media base path
        media_layout = QHBoxLayout()
        media_layout.setSpacing(SPACING["sm"])
        self._media_base_path = QLineEdit()
        self._media_base_path.setPlaceholderText(r"e.g., D:\inetpub\wwwroot\Bluestreak\Media")
        media_layout.addWidget(self._media_base_path)
        self._media_browse = QPushButton("Browse...")
        self._media_browse.clicked.connect(self._browse_media)
        media_layout.addWidget(self._media_browse)
        layout.addRow(
            self._create_label_with_info(
                "Media Base Path:",
                "Base directory where Bluestreak stores media files. "
                "File paths from the database are relative to this path."
            ),
            media_layout
        )

    def _load_settings(self) -> None:
        """Load settings into form fields."""
        settings = load_settings()

        # General tab
        self._theme_combo.setCurrentText(settings.theme)
        self._font_size_slider.setValue(settings.font_size)
        self._font_size_label.setText(f"{settings.font_size} pt")
        # Set UI scale dropdown (convert 100/125/150 to index)
        scale_map = {100: 0, 125: 1, 150: 2}
        self._scale_combo.setCurrentIndex(scale_map.get(settings.ui_scale, 0))
        # Cert warning date
        self._cert_warning_date_cleared = False
        if settings.cert_warning_date:
            self._cert_warning_date.setDate(QDate(
                settings.cert_warning_date.year,
                settings.cert_warning_date.month,
                settings.cert_warning_date.day
            ))
            self._cert_warning_date.setEnabled(True)
            self._cert_warning_clear.setText("Unset")
        else:
            self._cert_warning_date.setDate(QDate.currentDate())
            self._cert_warning_date.setEnabled(False)
            self._cert_warning_clear.setText("Set")
            self._cert_warning_date_cleared = True  # Mark as not set
        # Set history retention dropdown (map days to index)
        retention_map = {0: 0, 30: 1, 90: 2, 365: 3}
        self._history_retention.setCurrentIndex(retention_map.get(settings.history_retention_days, 2))

        # Account status checks
        self._check_credit_hold.setChecked(settings.check_credit_hold)
        self._check_cod_terms.setChecked(settings.check_cod_terms)

        # Database tab
        self._db_driver.setCurrentText(settings.db_driver)
        self._db_host.setText(settings.db_host)
        self._db_port.setValue(settings.db_port)
        self._db_database.setText(settings.db_database)
        self._db_username.setText(settings.db_username)
        self._db_password.setText(settings.db_password)
        self._db_sqlite_path.setText(settings.db_sqlite_path)
        self._search_limit.setValue(settings.search_result_limit)

        self._box_jwt_path.setText(settings.box_jwt_config_path)

        self._media_base_path.setText(settings.media_base_path)

        self._on_driver_changed(self._db_driver.currentText())

    def _save_settings(self) -> None:
        """Save form fields to settings."""
        settings = load_settings()

        # General tab
        settings.theme = self._theme_combo.currentText()
        settings.font_size = self._font_size_slider.value()
        # Convert UI scale dropdown index to value (100/125/150)
        scale_values = [100, 125, 150]
        settings.ui_scale = scale_values[self._scale_combo.currentIndex()]
        # Cert warning date
        if not self._cert_warning_date_cleared:
            qdate = self._cert_warning_date.date()
            settings.cert_warning_date = date(int(qdate.year()), int(qdate.month()), int(qdate.day()))
        else:
            settings.cert_warning_date = None
        # Convert history retention dropdown index to days
        retention_values = [0, 30, 90, 365]
        settings.history_retention_days = retention_values[self._history_retention.currentIndex()]

        # Account status checks
        settings.check_credit_hold = self._check_credit_hold.isChecked()
        settings.check_cod_terms = self._check_cod_terms.isChecked()

        # Database tab
        settings.db_driver = self._db_driver.currentText()
        settings.db_host = self._db_host.text()
        settings.db_port = self._db_port.value()
        settings.db_database = self._db_database.text()
        settings.db_username = self._db_username.text()
        settings.db_password = self._db_password.text()
        settings.db_sqlite_path = self._db_sqlite_path.text()
        settings.search_result_limit = self._search_limit.value()

        settings.box_jwt_config_path = self._box_jwt_path.text()

        settings.media_base_path = self._media_base_path.text()

        save_settings(settings)

    def _save_and_close(self) -> None:
        """Save settings and close dialog."""
        # Check if theme, font, or scale changed
        old_settings = load_settings()
        old_theme = old_settings.theme
        old_font = old_settings.font_size
        old_scale = old_settings.ui_scale

        new_theme = self._theme_combo.currentText()
        new_font = self._font_size_slider.value()
        scale_values = [100, 125, 150]
        new_scale = scale_values[self._scale_combo.currentIndex()]

        self._save_settings()

        # Notify user if theme/font/scale changed (requires restart for full effect)
        if old_theme != new_theme or old_font != new_font or old_scale != new_scale:
            QMessageBox.information(
                self,
                "Restart Required",
                "Theme, font, and UI scale changes will take full effect after restarting the application.",
            )

        self.accept()

    def _on_font_size_changed(self, value: int) -> None:
        """Update font size label when slider changes."""
        self._font_size_label.setText(f"{value} pt")

    def _toggle_cert_warning_date(self) -> None:
        """Toggle cert warning date between set and unset."""
        if self._cert_warning_date_cleared:
            # Re-enable the date picker
            self._cert_warning_date_cleared = False
            self._cert_warning_date.setEnabled(True)
            self._cert_warning_date.setDate(QDate.currentDate())
            self._cert_warning_clear.setText("Unset")
        else:
            # Disable/clear the date picker
            self._cert_warning_date_cleared = True
            self._cert_warning_date.setEnabled(False)
            self._cert_warning_clear.setText("Set")

    def _on_cert_warning_date_changed(self) -> None:
        """Reset cleared flag when user selects a date."""
        self._cert_warning_date_cleared = False
        self._cert_warning_clear.setText("Unset")

    def _on_driver_changed(self, driver: str) -> None:
        """Enable/disable fields based on driver selection."""
        is_sqlserver = driver == "sqlserver"
        self._db_host.setEnabled(is_sqlserver)
        self._db_port.setEnabled(is_sqlserver)
        self._db_database.setEnabled(is_sqlserver)
        self._db_username.setEnabled(is_sqlserver)
        self._db_password.setEnabled(is_sqlserver)
        self._db_sqlite_path.setEnabled(not is_sqlserver)
        self._db_sqlite_browse.setEnabled(not is_sqlserver)

    def _browse_sqlite(self) -> None:
        """Browse for SQLite database file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SQLite Database",
            "",
            "SQLite Database (*.db *.sqlite);;All Files (*)",
        )
        if path:
            self._db_sqlite_path.setText(path)

    def _browse_jwt(self) -> None:
        """Browse for JWT config file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Box JWT Config",
            "",
            "JSON Files (*.json);;All Files (*)",
        )
        if path:
            self._box_jwt_path.setText(path)

    def _browse_media(self) -> None:
        """Browse for media base directory."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Media Base Directory",
            self._media_base_path.text() or "",
        )
        if path:
            self._media_base_path.setText(path)

    def _test_db_connection(self) -> None:
        """Test database connection."""
        config = DatabaseConfig(
            driver=self._db_driver.currentText(),
            host=self._db_host.text(),
            port=self._db_port.value(),
            database=self._db_database.text(),
            username=self._db_username.text(),
            password=self._db_password.text(),
            sqlite_path=self._db_sqlite_path.text(),
        )

        success, message = check_connection(config)

        if success:
            QMessageBox.information(self, "Connection Test", f"Success: {message}")
        else:
            QMessageBox.warning(self, "Connection Test", f"Failed: {message}")

    def _test_box_connection(self) -> None:
        """Test Box.com connection."""
        jwt_path = self._box_jwt_path.text()
        if not jwt_path:
            QMessageBox.warning(self, "Connection Test", "Please specify a JWT config file.")
            return

        if not Path(jwt_path).exists():
            QMessageBox.warning(self, "Connection Test", "JWT config file not found.")
            return

        try:
            from box_service import BoxUploader

            uploader = BoxUploader(jwt_path)
            uploader.connect()
            user = uploader.get_current_user()
            QMessageBox.information(
                self,
                "Connection Test",
                f"Success: Connected as {user.name} ({user.login})",
            )
        except Exception as e:
            QMessageBox.warning(self, "Connection Test", f"Failed: {e}")
