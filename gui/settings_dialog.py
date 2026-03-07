"""Settings dialog with modern styling and three tabs: Database, Box.com, Paths."""

from pathlib import Path

from PySide6.QtCore import Qt
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
)

from PySide6.QtWidgets import QApplication

from settings import load_settings, save_settings
from database.connection import DatabaseConfig, check_connection
from gui.theme import SPACING, SIZES, get_icon


class SettingsDialog(QDialog):
    """Settings dialog with Database, Box, and Paths tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(SIZES["dialog_min_w"])
        self.setMinimumHeight(SIZES["dialog_min_h"])
        self._setup_ui()
        self._load_settings()

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

    def _create_help_label(self, text: str) -> QLabel:
        """Create a styled help text label."""
        label = QLabel(text)
        label.setObjectName("helpLabel")
        label.setWordWrap(True)
        return label

    def _setup_general_tab(self) -> None:
        layout = QFormLayout(self._general_tab)
        layout.setSpacing(SPACING["sm"])
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])

        # Theme selection
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["dark", "light"])
        self._theme_combo.setToolTip("Application color theme (requires restart)")
        layout.addRow("Theme:", self._theme_combo)

        # Font size slider
        font_size_layout = QHBoxLayout()
        font_size_layout.setSpacing(SPACING["sm"])

        self._font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self._font_size_slider.setRange(8, 16)
        self._font_size_slider.setValue(10)
        self._font_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._font_size_slider.setTickInterval(1)
        self._font_size_slider.setToolTip("Base font size for the application (requires restart)")
        self._font_size_slider.valueChanged.connect(self._on_font_size_changed)
        font_size_layout.addWidget(self._font_size_slider)

        self._font_size_label = QLabel("10 pt")
        self._font_size_label.setMinimumWidth(SIZES["label_min_w"])
        font_size_layout.addWidget(self._font_size_label)

        layout.addRow("Font Size:", font_size_layout)

        # UI Scale dropdown
        self._scale_combo = QComboBox()
        self._scale_combo.addItems(["100%", "125%", "150%"])
        self._scale_combo.setToolTip("Scale all UI elements (requires restart)")
        layout.addRow("UI Scale:", self._scale_combo)

        # Help text for theme/font/scale
        help_label = self._create_help_label(
            "Theme, font size, and UI scale changes require restarting the application to take effect."
        )
        layout.addRow("", help_label)

        # Warning days threshold
        self._warning_days = QSpinBox()
        self._warning_days.setRange(0, 365)
        self._warning_days.setValue(30)
        self._warning_days.setSuffix(" days")
        self._warning_days.setToolTip(
            "Warn if certification is older than this many days (0 = disabled)"
        )
        layout.addRow("Cert Age Warning:", self._warning_days)

    def _setup_db_tab(self) -> None:
        layout = QFormLayout(self._db_tab)
        layout.setSpacing(SPACING["sm"])
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])

        # Driver selection
        self._db_driver = QComboBox()
        self._db_driver.addItems(["sqlserver", "sqlite"])
        self._db_driver.currentTextChanged.connect(self._on_driver_changed)
        layout.addRow("Driver:", self._db_driver)

        # SQL Server fields
        self._db_host = QLineEdit()
        self._db_host.setPlaceholderText("e.g., 192.168.1.100")
        layout.addRow("Host:", self._db_host)

        self._db_port = QSpinBox()
        self._db_port.setRange(1, 65535)
        self._db_port.setValue(1433)
        layout.addRow("Port:", self._db_port)

        self._db_database = QLineEdit()
        self._db_database.setText("Bluestreak")
        layout.addRow("Database:", self._db_database)

        self._db_username = QLineEdit()
        layout.addRow("Username:", self._db_username)

        self._db_password = QLineEdit()
        self._db_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Password:", self._db_password)

        # SQLite path (for testing)
        sqlite_layout = QHBoxLayout()
        sqlite_layout.setSpacing(SPACING["sm"])
        self._db_sqlite_path = QLineEdit()
        self._db_sqlite_path.setPlaceholderText("Path to SQLite database")
        sqlite_layout.addWidget(self._db_sqlite_path)
        self._db_sqlite_browse = QPushButton("Browse...")
        self._db_sqlite_browse.setMaximumHeight(SIZES["btn_max_h"])
        self._db_sqlite_browse.clicked.connect(self._browse_sqlite)
        sqlite_layout.addWidget(self._db_sqlite_browse)
        layout.addRow("SQLite Path:", sqlite_layout)

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
        self._search_limit.setToolTip(
            "Maximum number of distinct orders to return when searching by partial order ID"
        )
        layout.addRow("Search Result Limit:", self._search_limit)

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
        self._box_jwt_browse.setMaximumHeight(SIZES["btn_max_h"])
        self._box_jwt_browse.clicked.connect(self._browse_jwt)
        jwt_layout.addWidget(self._box_jwt_browse)
        layout.addRow("JWT Config:", jwt_layout)

        # Help text
        help_label = self._create_help_label(
            "The JWT config file can be downloaded from your Box Developer Console.\n"
            "Go to: Developer Console > Your App > Configuration > Generate a Public/Private Keypair"
        )
        layout.addRow("", help_label)

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
        self._media_browse.setMaximumHeight(SIZES["btn_max_h"])
        self._media_browse.clicked.connect(self._browse_media)
        media_layout.addWidget(self._media_browse)
        layout.addRow("Media Base Path:", media_layout)

        # Help text
        help_label = self._create_help_label(
            "This is the base directory where Bluestreak stores media files.\n"
            "File paths from the database (e.g., '202602/file.pdf') are relative to this path."
        )
        layout.addRow("", help_label)

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
        self._warning_days.setValue(settings.warning_days_threshold)

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
        settings.warning_days_threshold = self._warning_days.value()

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
