#!/usr/bin/env python3
"""CLI for Bluestreak Box Uploader - used for testing and development."""

import argparse
import sys
from pathlib import Path

from database.connection import DatabaseConfig, check_connection
from database.queries import query_order_with_customer
from database.sqlite_seed import seed_database


def cmd_query(args) -> int:
    """Query certifications for an order."""
    config = DatabaseConfig(
        driver=args.driver,
        host=args.host,
        port=args.port,
        database=args.database,
        username=args.username,
        password=args.password,
        sqlite_path=args.sqlite,
    )

    print(f"Querying order {args.order_id}...")

    try:
        certs, customer = query_order_with_customer(config, args.order_id)
    except Exception as e:
        print(f"Error: {e}")
        return 1

    if not certs:
        print("No certifications found for this order.")
        return 0

    print(f"\nCustomer: {customer.cst_name if customer else 'Unknown'}")
    if customer:
        if customer.cst_integration_id:
            print(f"Box Folder ID: {customer.cst_integration_id}")
        else:
            print("WARNING: Customer not mapped to Box folder (cstIntegrationID is null)")

    print(f"\nFound {len(certs)} certification(s):\n")

    for cert in certs:
        print(f"  [{cert.crt_cert_no}]")
        print(f"    ID: {cert.crt_id}")
        print(f"    PO#: {cert.crt_po_number or 'N/A'}")
        print(f"    Files: {len(cert.media_files)}")
        for mf in cert.media_files:
            print(f"      - {mf.med_full_path}")
        print()

    total_files = sum(len(c.media_files) for c in certs)
    print(f"Total: {len(certs)} certs, {total_files} files")

    return 0


def cmd_test_db(args) -> int:
    """Test database connection."""
    config = DatabaseConfig(
        driver=args.driver,
        host=args.host,
        port=args.port,
        database=args.database,
        username=args.username,
        password=args.password,
        sqlite_path=args.sqlite,
    )

    print(f"Testing {args.driver} connection...")
    success, message = check_connection(config)

    if success:
        print(f"SUCCESS: {message}")
        return 0
    else:
        print(f"FAILED: {message}")
        return 1


def cmd_test_box(args) -> int:
    """Test Box.com connection."""
    from box_service import BoxUploader

    print(f"Testing Box connection with config: {args.config}")

    try:
        uploader = BoxUploader(args.config)
        uploader.connect()
        user = uploader.get_current_user()
        print(f"SUCCESS: Connected as {user.name} ({user.login})")
        return 0
    except Exception as e:
        print(f"FAILED: {e}")
        return 1


def cmd_seed(args) -> int:
    """Seed SQLite database with sample data."""
    db_path = args.output or "test.db"
    print(f"Seeding database: {db_path}")
    seed_database(db_path)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bluestreak Box Uploader CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query certifications for an order")
    query_parser.add_argument("order_id", type=int, help="Order ID to query")
    query_parser.add_argument("--driver", default="sqlite", choices=["sqlite", "sqlserver"])
    query_parser.add_argument("--sqlite", default="test.db", help="SQLite database path")
    query_parser.add_argument("--host", default="", help="SQL Server host")
    query_parser.add_argument("--port", type=int, default=1433, help="SQL Server port")
    query_parser.add_argument("--database", default="Bluestreak", help="Database name")
    query_parser.add_argument("--username", default="", help="Database username")
    query_parser.add_argument("--password", default="", help="Database password")
    query_parser.set_defaults(func=cmd_query)

    # Test DB command
    testdb_parser = subparsers.add_parser("test-db", help="Test database connection")
    testdb_parser.add_argument("--driver", default="sqlite", choices=["sqlite", "sqlserver"])
    testdb_parser.add_argument("--sqlite", default="test.db", help="SQLite database path")
    testdb_parser.add_argument("--host", default="", help="SQL Server host")
    testdb_parser.add_argument("--port", type=int, default=1433, help="SQL Server port")
    testdb_parser.add_argument("--database", default="Bluestreak", help="Database name")
    testdb_parser.add_argument("--username", default="", help="Database username")
    testdb_parser.add_argument("--password", default="", help="Database password")
    testdb_parser.set_defaults(func=cmd_test_db)

    # Test Box command
    testbox_parser = subparsers.add_parser("test-box", help="Test Box.com connection")
    testbox_parser.add_argument("--config", required=True, help="Path to Box JWT config JSON")
    testbox_parser.set_defaults(func=cmd_test_box)

    # Seed command
    seed_parser = subparsers.add_parser("seed", help="Seed SQLite database with sample data")
    seed_parser.add_argument("--output", "-o", help="Output database path (default: test.db)")
    seed_parser.set_defaults(func=cmd_seed)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
