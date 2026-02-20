"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path

from database.sqlite_seed import seed_database
from database.connection import DatabaseConfig


@pytest.fixture
def test_db(tmp_path) -> Path:
    """Create a seeded test database."""
    db_path = tmp_path / "test.db"
    seed_database(db_path)
    return db_path


@pytest.fixture
def sqlite_config(test_db) -> DatabaseConfig:
    """Get a DatabaseConfig for the test SQLite database."""
    return DatabaseConfig(
        driver="sqlite",
        sqlite_path=str(test_db),
    )


@pytest.fixture
def fixture_db() -> Path:
    """Path to the committed test database fixture."""
    return Path(__file__).parent / "fixtures" / "test.db"


@pytest.fixture
def fixture_config(fixture_db) -> DatabaseConfig:
    """Config using committed fixture database."""
    return DatabaseConfig(driver="sqlite", sqlite_path=str(fixture_db))


@pytest.fixture
def media_base_path() -> Path:
    """Path to test media files."""
    return Path(__file__).parent / "fixtures" / "media"
