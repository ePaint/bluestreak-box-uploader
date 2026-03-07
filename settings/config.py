"""TOML-based settings persistence for Bluestreak Box Uploader."""

import sys
import tomllib
from pathlib import Path
from typing import Literal

import tomli_w
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings with validation."""

    # Database settings
    db_driver: Literal["sqlserver", "sqlite"] = "sqlserver"
    db_host: str = ""
    db_port: int = Field(default=1433, ge=1, le=65535)
    db_database: str = "Bluestreak"
    db_username: str = ""
    db_password: str = ""
    db_sqlite_path: str = ""

    # Box settings
    box_jwt_config_path: str = ""

    # Paths
    media_base_path: str = r"D:\inetpub\wwwroot\Bluestreak\Media"

    # UI settings
    auto_upload_single: bool = True
    last_order_id: str = ""
    theme: Literal["dark", "light"] = "dark"
    font_size: int = Field(default=10, ge=8, le=16)
    ui_scale: Literal[100, 125, 150] = 100

    # Search settings
    search_result_limit: int = Field(default=100, ge=10, le=1000)

    # Warning settings
    warning_days_threshold: int = Field(default=30, ge=0, le=365)

    # UI state (not shown in settings dialog)
    cert_table_column_widths: list[int] | None = None


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


def load_settings() -> Settings:
    """Load settings from settings.toml, return defaults if not found."""
    settings_path = _get_settings_path()
    if settings_path.exists():
        with open(settings_path, "rb") as f:
            loaded = tomllib.load(f)
            return Settings.model_validate(loaded)
    return Settings()


def save_settings(settings: Settings) -> None:
    """Save settings to settings.toml in app data directory."""
    settings_path = _get_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "wb") as f:
        tomli_w.dump(settings.model_dump(exclude_none=True), f)


def get_database_config():
    """Get DatabaseConfig from current settings."""
    from database.connection import DatabaseConfig

    settings = load_settings()
    return DatabaseConfig(
        driver=settings.db_driver,
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_database,
        username=settings.db_username,
        password=settings.db_password,
        sqlite_path=settings.db_sqlite_path,
    )
