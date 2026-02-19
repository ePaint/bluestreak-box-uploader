"""Tests for database layer."""

import pytest

from database.connection import get_connection, check_connection
from database.queries import query_certifications_by_order, get_customer_by_id


class TestConnection:
    """Tests for database connection."""

    def test_sqlite_connection(self, sqlite_config):
        """Test SQLite connection works."""
        success, message = check_connection(sqlite_config)
        assert success, f"Connection failed: {message}"

    def test_sqlite_param_conversion(self, sqlite_config):
        """Test @param to ? conversion for SQLite."""
        conn = get_connection(sqlite_config)
        cursor = conn.cursor()

        # Test with named parameter
        cursor.execute("SELECT * FROM Customer WHERE cstID = @CustomerID", {"CustomerID": 1916})
        row = cursor.fetchone()

        assert row is not None
        assert row[1] == "Burton Industries Inc."

        cursor.close()
        conn.close()


class TestQueries:
    """Tests for database queries."""

    def test_query_certifications_by_order(self, sqlite_config):
        """Test querying certifications for an order."""
        conn = get_connection(sqlite_config)
        certs = query_certifications_by_order(conn, 444337)
        conn.close()

        assert len(certs) == 6, f"Expected 6 certifications, got {len(certs)}"

        # Check first cert
        cert1 = next(c for c in certs if c.crt_cert_no == "444337-1")
        assert cert1.crt_cust_name == "Burton Industries Inc."
        assert cert1.crt_po_number == "123456TEST"
        assert len(cert1.media_files) == 1

        # Check cert with multiple files
        cert6 = next(c for c in certs if c.crt_cert_no == "444337-2-3")
        assert len(cert6.media_files) == 4

    def test_query_nonexistent_order(self, sqlite_config):
        """Test querying non-existent order returns empty list."""
        conn = get_connection(sqlite_config)
        certs = query_certifications_by_order(conn, 999999)
        conn.close()

        assert len(certs) == 0

    def test_get_customer_by_id(self, sqlite_config):
        """Test getting customer by ID."""
        conn = get_connection(sqlite_config)
        customer = get_customer_by_id(conn, 1916)
        conn.close()

        assert customer is not None
        assert customer.cst_name == "Burton Industries Inc."
        # Note: cst_integration_id is NULL in test data
        assert customer.cst_integration_id is None

    def test_get_nonexistent_customer(self, sqlite_config):
        """Test getting non-existent customer returns None."""
        conn = get_connection(sqlite_config)
        customer = get_customer_by_id(conn, 999999)
        conn.close()

        assert customer is None


class TestMediaFiles:
    """Tests for media file handling."""

    def test_media_file_paths(self, sqlite_config):
        """Test media file paths are correctly retrieved."""
        conn = get_connection(sqlite_config)
        certs = query_certifications_by_order(conn, 444337)
        conn.close()

        cert1 = next(c for c in certs if c.crt_cert_no == "444337-1")
        assert len(cert1.media_files) == 1

        media = cert1.media_files[0]
        assert media.med_full_path == "202602/ApprovedCert_444337-1_263756.pdf"
        assert "Approved Certification" in media.med_description

    def test_total_file_count(self, sqlite_config):
        """Test total file count across all certifications."""
        conn = get_connection(sqlite_config)
        certs = query_certifications_by_order(conn, 444337)
        conn.close()

        total_files = sum(len(c.media_files) for c in certs)
        assert total_files == 14, f"Expected 14 total files, got {total_files}"
