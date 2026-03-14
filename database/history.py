"""SQLite-based upload history persistence."""

import csv
import sqlite3
import uuid
from datetime import date, datetime
from pathlib import Path

from database.models import UploadHistoryRecord
from settings.config import _get_app_data_dir


def get_history_db_path() -> Path:
    """Get path to the upload history database."""
    return _get_app_data_dir() / "upload_history.db"


def init_history_db() -> None:
    """Initialize the history database, creating tables if needed."""
    db_path = get_history_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS upload_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(36) NOT NULL,
                timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                order_id INTEGER NOT NULL,
                cert_no VARCHAR(25) NOT NULL,
                filename VARCHAR(500) NOT NULL,
                box_file_id VARCHAR(50),
                status VARCHAR(20) NOT NULL,
                error_msg TEXT,
                customer_name VARCHAR(100),
                po_number VARCHAR(50),
                file_size INTEGER
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_timestamp
            ON upload_history(timestamp DESC)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_session
            ON upload_history(session_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_order
            ON upload_history(order_id)
        """)

        # Migration: add po_number column if it doesn't exist
        cursor = conn.execute("PRAGMA table_info(upload_history)")
        columns = [row[1] for row in cursor.fetchall()]
        if "po_number" not in columns:
            conn.execute("ALTER TABLE upload_history ADD COLUMN po_number VARCHAR(50)")

        conn.commit()
    finally:
        conn.close()


def generate_session_id() -> str:
    """Generate a new session ID for an upload batch."""
    return str(uuid.uuid4())


def record_upload(record: UploadHistoryRecord) -> int:
    """Record a single upload to history. Returns the inserted ID."""
    db_path = get_history_db_path()
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT INTO upload_history (
                session_id, timestamp, order_id, cert_no, filename,
                box_file_id, status, error_msg, customer_name, po_number, file_size
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.session_id,
                record.timestamp or datetime.now(),
                record.order_id,
                record.cert_no,
                record.filename,
                record.box_file_id,
                record.status,
                record.error_msg,
                record.customer_name,
                record.po_number,
                record.file_size,
            ),
        )
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def _row_to_record(row: tuple) -> UploadHistoryRecord:
    """Convert a database row to UploadHistoryRecord."""
    # Note: po_number was added via ALTER TABLE migration, so it's at index 11
    return UploadHistoryRecord(
        id=row[0],
        session_id=row[1],
        timestamp=datetime.fromisoformat(row[2]) if row[2] else None,
        order_id=row[3],
        cert_no=row[4],
        filename=row[5],
        box_file_id=row[6],
        status=row[7],
        error_msg=row[8],
        customer_name=row[9],
        file_size=row[10],
        po_number=row[11] if len(row) > 11 else None,
    )


def search_history(
    query: str = "",
    status: str | None = None,
    limit: int = 500,
) -> list[UploadHistoryRecord]:
    """Search upload history with optional filters.

    Args:
        query: Search term (matches order_id, cert_no, filename, customer_name)
        status: Filter by status ('success', 'failed', or None for all)
        limit: Maximum records to return

    Returns:
        List of matching records, newest first
    """
    db_path = get_history_db_path()
    if not db_path.exists():
        return []

    conn = sqlite3.connect(db_path)
    try:
        sql = "SELECT * FROM upload_history WHERE 1=1"
        params: list = []

        if query:
            sql += """ AND (
                CAST(order_id AS TEXT) LIKE ?
                OR cert_no LIKE ?
                OR filename LIKE ?
                OR customer_name LIKE ?
                OR po_number LIKE ?
            )"""
            like_query = f"%{query}%"
            params.extend([like_query, like_query, like_query, like_query, like_query])

        if status:
            sql += " AND status = ?"
            params.append(status)

        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(sql, params)
        return [_row_to_record(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_history_grouped_by_date(days: int = 30) -> dict[date, list[UploadHistoryRecord]]:
    """Get history grouped by date.

    Args:
        days: Number of days to look back

    Returns:
        Dictionary mapping dates to list of records
    """
    db_path = get_history_db_path()
    if not db_path.exists():
        return {}

    conn = sqlite3.connect(db_path)
    try:
        cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = cutoff.replace(day=cutoff.day - days) if days > 0 else datetime.min

        cursor = conn.execute(
            """
            SELECT * FROM upload_history
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            """,
            (cutoff,),
        )

        grouped: dict[date, list[UploadHistoryRecord]] = {}
        for row in cursor.fetchall():
            record = _row_to_record(row)
            if record.timestamp:
                record_date = record.timestamp.date()
                if record_date not in grouped:
                    grouped[record_date] = []
                grouped[record_date].append(record)

        return grouped
    finally:
        conn.close()


def get_session_records(session_id: str) -> list[UploadHistoryRecord]:
    """Get all records for a specific session."""
    db_path = get_history_db_path()
    if not db_path.exists():
        return []

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            "SELECT * FROM upload_history WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )
        return [_row_to_record(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def clear_history_before(before_date: datetime) -> int:
    """Clear history older than the specified date. Returns count deleted."""
    db_path = get_history_db_path()
    if not db_path.exists():
        return 0

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            "DELETE FROM upload_history WHERE timestamp < ?",
            (before_date,),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def clear_all_history() -> int:
    """Clear all history. Returns count deleted."""
    db_path = get_history_db_path()
    if not db_path.exists():
        return 0

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("DELETE FROM upload_history")
        count = cursor.rowcount
        conn.commit()
        return count
    finally:
        conn.close()


def cleanup_old_history() -> int:
    """Auto-cleanup based on retention setting. Returns count deleted."""
    from datetime import timedelta

    from settings import load_settings

    settings = load_settings()
    if settings.history_retention_days > 0:
        cutoff = datetime.now() - timedelta(days=settings.history_retention_days)
        return clear_history_before(cutoff)
    return 0


def export_history_to_csv(records: list[UploadHistoryRecord], filepath: Path) -> None:
    """Export records to CSV file."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp",
            "Order ID",
            "Cert No",
            "Customer",
            "PO#",
            "Filename",
            "Status",
            "Error",
            "Box File ID",
            "File Size",
            "Session ID",
        ])
        for r in records:
            writer.writerow([
                r.timestamp.isoformat() if r.timestamp else "",
                r.order_id,
                r.cert_no,
                r.customer_name or "",
                r.po_number or "",
                r.filename,
                r.status,
                r.error_msg or "",
                r.box_file_id or "",
                r.file_size or "",
                r.session_id,
            ])
