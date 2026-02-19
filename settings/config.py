"""TOML-based settings persistence for Bluestreak Box Uploader."""

import sys
import tomllib
from pathlib import Path

import tomli_w


def _get_app_data_dir() -> Path:
    """Get the application data directory for storing settings."""
    if sys.platform == "darwin":
        app_dir = Path.home() / "Library" / "Application Support" / "BluestreakBoxUploader"
    elif sys.platform == "win32":
        import os

        app_dir = Path(os.environ.get("APPDATA", Path.home())) / "BluestreakBoxUploader"
    else:
        app_dir = Path.home() / ".config" / "bluestreakboxuploader"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def _get_settings_path() -> Path:
    """Get the path to settings.toml, preferring local file for development."""
    local_path = Path.cwd() / "settings.toml"
    if local_path.exists():
        return local_path
    return _get_app_data_dir() / "settings.toml"


DEFAULT_SETTINGS: dict = {
    # Database settings
    "db_driver": "sqlserver",
    "db_host": "",
    "db_port": 1433,
    "db_database": "Bluestreak",
    "db_username": "",
    "db_password": "",
    "db_sqlite_path": "",
    # Box settings
    "box_jwt_config_path": "",
    # Paths
    "media_base_path": r"D:\inetpub\wwwroot\Bluestreak\Media",
    # UI settings
    "auto_upload_single": True,
    "last_order_id": "",
}


def load_settings() -> dict:
    """Load settings from settings.toml, return defaults if not found."""
    settings_path = _get_settings_path()
    if settings_path.exists():
        with open(settings_path, "rb") as f:
            loaded = tomllib.load(f)
            # Merge with defaults to handle new settings
            merged = DEFAULT_SETTINGS.copy()
            merged.update(loaded)
            return merged
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """Save settings to settings.toml in app data directory."""
    settings_path = _get_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "wb") as f:
        tomli_w.dump(settings, f)


def get_database_config():
    """Get DatabaseConfig from current settings."""
    from database.connection import DatabaseConfig

    settings = load_settings()
    return DatabaseConfig(
        driver=settings.get("db_driver", "sqlserver"),
        host=settings.get("db_host", ""),
        port=settings.get("db_port", 1433),
        database=settings.get("db_database", "Bluestreak"),
        username=settings.get("db_username", ""),
        password=settings.get("db_password", ""),
        sqlite_path=settings.get("db_sqlite_path", ""),
    )
