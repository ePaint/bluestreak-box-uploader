"""Settings dialog with three tabs: Database, Box.com, Paths."""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QLabel,
    QDialogButtonBox,
)

from settings import load_settings, save_settings
from database.connection import DatabaseConfig, check_connection


class SettingsDialog(QDialog):
    """Settings dialog with Database, Box, and Paths tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Tab widget
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # Database tab
        self._db_tab = QWidget()
        self._setup_db_tab()
        self._tabs.addTab(self._db_tab, "Database")

        # Box tab
        self._box_tab = QWidget()
        self._setup_box_tab()
        self._tabs.addTab(self._box_tab, "Box.com")

        # Paths tab
        self._paths_tab = QWidget()
        self._setup_paths_tab()
        self._tabs.addTab(self._paths_tab, "Paths")

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save_and_close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _setup_db_tab(self) -> None:
        layout = QFormLayout(self._db_tab)

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
        self._db_sqlite_path = QLineEdit()
        self._db_sqlite_path.setPlaceholderText("Path to SQLite database")
        sqlite_layout.addWidget(self._db_sqlite_path)
        self._db_sqlite_browse = QPushButton("Browse...")
        self._db_sqlite_browse.clicked.connect(self._browse_sqlite)
        sqlite_layout.addWidget(self._db_sqlite_browse)
        layout.addRow("SQLite Path:", sqlite_layout)

        # Test button
        self._db_test_btn = QPushButton("Test Connection")
        self._db_test_btn.clicked.connect(self._test_db_connection)
        layout.addRow("", self._db_test_btn)

    def _setup_box_tab(self) -> None:
        layout = QFormLayout(self._box_tab)

        # JWT config path
        jwt_layout = QHBoxLayout()
        self._box_jwt_path = QLineEdit()
        self._box_jwt_path.setPlaceholderText("Path to Box JWT config JSON file")
        jwt_layout.addWidget(self._box_jwt_path)
        self._box_jwt_browse = QPushButton("Browse...")
        self._box_jwt_browse.clicked.connect(self._browse_jwt)
        jwt_layout.addWidget(self._box_jwt_browse)
        layout.addRow("JWT Config:", jwt_layout)

        # Help text
        help_label = QLabel(
            "The JWT config file can be downloaded from your Box Developer Console.\n"
            "Go to: Developer Console > Your App > Configuration > Generate a Public/Private Keypair"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addRow("", help_label)

        # Test button
        self._box_test_btn = QPushButton("Test Connection")
        self._box_test_btn.clicked.connect(self._test_box_connection)
        layout.addRow("", self._box_test_btn)

    def _setup_paths_tab(self) -> None:
        layout = QFormLayout(self._paths_tab)

        # Media base path
        media_layout = QHBoxLayout()
        self._media_base_path = QLineEdit()
        self._media_base_path.setPlaceholderText(r"e.g., D:\inetpub\wwwroot\Bluestreak\Media")
        media_layout.addWidget(self._media_base_path)
        self._media_browse = QPushButton("Browse...")
        self._media_browse.clicked.connect(self._browse_media)
        media_layout.addWidget(self._media_browse)
        layout.addRow("Media Base Path:", media_layout)

        # Help text
        help_label = QLabel(
            "This is the base directory where Bluestreak stores media files.\n"
            "File paths from the database (e.g., '202602/file.pdf') are relative to this path."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addRow("", help_label)

    def _load_settings(self) -> None:
        """Load settings into form fields."""
        settings = load_settings()

        self._db_driver.setCurrentText(settings.get("db_driver", "sqlserver"))
        self._db_host.setText(settings.get("db_host", ""))
        self._db_port.setValue(settings.get("db_port", 1433))
        self._db_database.setText(settings.get("db_database", "Bluestreak"))
        self._db_username.setText(settings.get("db_username", ""))
        self._db_password.setText(settings.get("db_password", ""))
        self._db_sqlite_path.setText(settings.get("db_sqlite_path", ""))

        self._box_jwt_path.setText(settings.get("box_jwt_config_path", ""))

        self._media_base_path.setText(settings.get("media_base_path", ""))

        self._on_driver_changed(self._db_driver.currentText())

    def _save_settings(self) -> None:
        """Save form fields to settings."""
        settings = load_settings()

        settings["db_driver"] = self._db_driver.currentText()
        settings["db_host"] = self._db_host.text()
        settings["db_port"] = self._db_port.value()
        settings["db_database"] = self._db_database.text()
        settings["db_username"] = self._db_username.text()
        settings["db_password"] = self._db_password.text()
        settings["db_sqlite_path"] = self._db_sqlite_path.text()

        settings["box_jwt_config_path"] = self._box_jwt_path.text()

        settings["media_base_path"] = self._media_base_path.text()

        save_settings(settings)

    def _save_and_close(self) -> None:
        """Save settings and close dialog."""
        self._save_settings()
        self.accept()

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
