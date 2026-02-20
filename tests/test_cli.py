"""End-to-end tests for CLI commands."""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE_DB = FIXTURES_DIR / "test.db"


def run_cli(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    """Run the CLI with the given arguments."""
    cmd = [sys.executable, "cli.py", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


class TestCLIQuery:
    """Tests for the 'query' command."""

    def test_query_existing_order(self):
        """Test querying an order that exists."""
        result = run_cli("query", "444337", "--sqlite", str(FIXTURE_DB))

        assert result.returncode == 0
        assert "Found 6 certification(s)" in result.stdout

    def test_query_nonexistent_order(self):
        """Test querying an order that doesn't exist."""
        result = run_cli("query", "999999", "--sqlite", str(FIXTURE_DB))

        assert result.returncode == 0
        assert "No certifications found" in result.stdout

    def test_query_shows_customer_info(self):
        """Test that query output includes customer information."""
        result = run_cli("query", "444337", "--sqlite", str(FIXTURE_DB))

        assert result.returncode == 0
        assert "Customer:" in result.stdout

    def test_query_shows_media_files(self):
        """Test that query output includes media file paths."""
        result = run_cli("query", "444337", "--sqlite", str(FIXTURE_DB))

        assert result.returncode == 0
        assert ".pdf" in result.stdout or ".jpg" in result.stdout


class TestCLITestDb:
    """Tests for the 'test-db' command."""

    def test_sqlite_connection_success(self):
        """Test database connection check with valid database."""
        result = run_cli("test-db", "--sqlite", str(FIXTURE_DB))

        assert result.returncode == 0
        assert "SUCCESS" in result.stdout

    def test_sqlite_connection_with_new_db(self):
        """Test database connection check creates db if needed (SQLite behavior)."""
        # SQLite auto-creates databases, so this succeeds
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "new.db"
            result = run_cli("test-db", "--sqlite", str(db_path))

            assert result.returncode == 0
            assert "SUCCESS" in result.stdout


class TestCLISeed:
    """Tests for the 'seed' command."""

    def test_seed_creates_database(self):
        """Test seeding creates a valid database."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "new.db"

            result = run_cli("seed", "-o", str(db_path))

            assert result.returncode == 0
            assert db_path.exists()

    def test_seed_database_is_queryable(self):
        """Test that seeded database can be queried."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "seeded.db"

            # Seed the database
            run_cli("seed", "-o", str(db_path), check=True)

            # Query it
            result = run_cli("query", "444337", "--sqlite", str(db_path))

            assert result.returncode == 0
            assert "certification(s)" in result.stdout


class TestCLIHelp:
    """Tests for CLI help and error handling."""

    def test_no_command_shows_help(self):
        """Test that running without a command shows help."""
        result = run_cli()

        assert result.returncode == 1
        assert "usage:" in result.stdout.lower() or "usage:" in result.stderr.lower()

    def test_query_missing_order_id(self):
        """Test that query without order_id shows error."""
        result = run_cli("query")

        assert result.returncode != 0
