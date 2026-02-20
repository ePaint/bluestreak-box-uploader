"""SQL queries for Bluestreak database."""

from database.connection import DatabaseConnection, DatabaseConfig, get_connection
from database.models import Certification, MediaFile, Customer


# Main query to get certifications and media files for an order
# CTE names prefixed to avoid conflicts with table names (required for SQLite)
CERTIFICATIONS_QUERY = """
WITH CTE_Cert AS (
    SELECT
        crtCertNo,
        crtCustName,
        crt_cstID,
        crtPONumber,
        crtID,
        crt_orID
    FROM Certification
    WHERE crt_orID = @OrderID
),
CTE_Note AS (
    SELECT
        notID,
        not_crtID
    FROM Note
    WHERE not_crtID IN (SELECT crtID FROM CTE_Cert)
),
CTE_MediaXref AS (
    SELECT
        medxID,
        medx_medID,
        medx_notID,
        medx_crtID
    FROM MediaXref
    WHERE medx_notID IN (SELECT notID FROM CTE_Note)
       OR medx_crtID IN (SELECT crtID FROM CTE_Cert)
),
CTE_Media AS (
    SELECT
        medID,
        medDescription,
        medFullPath
    FROM Media
    WHERE medID IN (SELECT medx_medID FROM CTE_MediaXref)
)
SELECT
    c.crtCertNo,
    c.crtCustName,
    c.crt_cstID,
    c.crtPONumber,
    c.crtID,
    c.crt_orID,
    n.notID,
    mx.medxID,
    m.medID,
    m.medDescription,
    m.medFullPath
FROM CTE_Cert c
LEFT JOIN CTE_Note n ON n.not_crtID = c.crtID
LEFT JOIN CTE_MediaXref mx ON mx.medx_notID = n.notID OR mx.medx_crtID = c.crtID
LEFT JOIN CTE_Media m ON m.medID = mx.medx_medID
ORDER BY c.crtCertNo, mx.medxID
"""

CUSTOMER_QUERY = """
SELECT
    cstID,
    cstName,
    cstIntegrationID
FROM Customer
WHERE cstID = @CustomerID
"""

# Partial order search queries (different syntax for SQL Server vs SQLite)
PARTIAL_ORDER_SEARCH_SQLSERVER = """
WITH CTE_Orders AS (
    SELECT DISTINCT TOP(@Limit) crt_orID
    FROM Certification
    WHERE CAST(crt_orID AS VARCHAR) LIKE @SearchPattern
    ORDER BY crt_orID DESC
),
CTE_Cert AS (
    SELECT
        crtCertNo,
        crtCustName,
        crt_cstID,
        crtPONumber,
        crtID,
        crt_orID
    FROM Certification
    WHERE crt_orID IN (SELECT crt_orID FROM CTE_Orders)
),
CTE_Note AS (
    SELECT
        notID,
        not_crtID
    FROM Note
    WHERE not_crtID IN (SELECT crtID FROM CTE_Cert)
),
CTE_MediaXref AS (
    SELECT
        medxID,
        medx_medID,
        medx_notID,
        medx_crtID
    FROM MediaXref
    WHERE medx_notID IN (SELECT notID FROM CTE_Note)
       OR medx_crtID IN (SELECT crtID FROM CTE_Cert)
),
CTE_Media AS (
    SELECT
        medID,
        medDescription,
        medFullPath
    FROM Media
    WHERE medID IN (SELECT medx_medID FROM CTE_MediaXref)
)
SELECT
    c.crtCertNo,
    c.crtCustName,
    c.crt_cstID,
    c.crtPONumber,
    c.crtID,
    c.crt_orID,
    n.notID,
    mx.medxID,
    m.medID,
    m.medDescription,
    m.medFullPath
FROM CTE_Cert c
LEFT JOIN CTE_Note n ON n.not_crtID = c.crtID
LEFT JOIN CTE_MediaXref mx ON mx.medx_notID = n.notID OR mx.medx_crtID = c.crtID
LEFT JOIN CTE_Media m ON m.medID = mx.medx_medID
ORDER BY c.crt_orID DESC, c.crtCertNo, mx.medxID
"""

PARTIAL_ORDER_SEARCH_SQLITE = """
WITH CTE_Orders AS (
    SELECT DISTINCT crt_orID
    FROM Certification
    WHERE CAST(crt_orID AS TEXT) LIKE @SearchPattern
    ORDER BY crt_orID DESC
    LIMIT @Limit
),
CTE_Cert AS (
    SELECT
        crtCertNo,
        crtCustName,
        crt_cstID,
        crtPONumber,
        crtID,
        crt_orID
    FROM Certification
    WHERE crt_orID IN (SELECT crt_orID FROM CTE_Orders)
),
CTE_Note AS (
    SELECT
        notID,
        not_crtID
    FROM Note
    WHERE not_crtID IN (SELECT crtID FROM CTE_Cert)
),
CTE_MediaXref AS (
    SELECT
        medxID,
        medx_medID,
        medx_notID,
        medx_crtID
    FROM MediaXref
    WHERE medx_notID IN (SELECT notID FROM CTE_Note)
       OR medx_crtID IN (SELECT crtID FROM CTE_Cert)
),
CTE_Media AS (
    SELECT
        medID,
        medDescription,
        medFullPath
    FROM Media
    WHERE medID IN (SELECT medx_medID FROM CTE_MediaXref)
)
SELECT
    c.crtCertNo,
    c.crtCustName,
    c.crt_cstID,
    c.crtPONumber,
    c.crtID,
    c.crt_orID,
    n.notID,
    mx.medxID,
    m.medID,
    m.medDescription,
    m.medFullPath
FROM CTE_Cert c
LEFT JOIN CTE_Note n ON n.not_crtID = c.crtID
LEFT JOIN CTE_MediaXref mx ON mx.medx_notID = n.notID OR mx.medx_crtID = c.crtID
LEFT JOIN CTE_Media m ON m.medID = mx.medx_medID
ORDER BY c.crt_orID DESC, c.crtCertNo, mx.medxID
"""


def query_certifications_by_order(
    conn: DatabaseConnection, order_id: int
) -> list[Certification]:
    """Query certifications and their media files for an order."""
    cursor = conn.cursor()
    cursor.execute(CERTIFICATIONS_QUERY, {"OrderID": order_id})
    rows = cursor.fetchall()
    cursor.close()

    # Group results by certification
    certs_dict: dict[int, Certification] = {}
    seen_media: set[tuple[int, int]] = set()  # (crt_id, med_id)

    for row in rows:
        crt_id = row[4]  # crtID

        if crt_id not in certs_dict:
            certs_dict[crt_id] = Certification(
                crt_id=crt_id,
                crt_cert_no=row[0],  # crtCertNo
                crt_cust_name=row[1],  # crtCustName
                crt_cst_id=row[2],  # crt_cstID
                crt_po_number=row[3],  # crtPONumber
                crt_or_id=row[5],  # crt_orID
                media_files=[],
            )

        # Add media file if present and not already added
        med_id = row[8]  # medID
        if med_id is not None:
            key = (crt_id, med_id)
            if key not in seen_media:
                seen_media.add(key)
                media_file = MediaFile(
                    med_id=med_id,
                    med_description=row[9],  # medDescription
                    med_full_path=row[10],  # medFullPath
                    medx_id=row[7],  # medxID
                    not_id=row[6],  # notID
                )
                certs_dict[crt_id].media_files.append(media_file)

    return list(certs_dict.values())


def get_customer_by_id(conn: DatabaseConnection, customer_id: int) -> Customer | None:
    """Get customer by ID."""
    cursor = conn.cursor()
    cursor.execute(CUSTOMER_QUERY, {"CustomerID": customer_id})
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return None

    return Customer(
        cst_id=row[0],
        cst_name=row[1],
        cst_integration_id=row[2],
    )


def query_order_with_customer(
    config: DatabaseConfig, order_id: int
) -> tuple[list[Certification], Customer | None]:
    """Query certifications and customer info for an order."""
    conn = get_connection(config)
    try:
        certs = query_certifications_by_order(conn, order_id)

        # Get customer from first certification
        customer = None
        if certs:
            customer = get_customer_by_id(conn, certs[0].crt_cst_id)

        return certs, customer
    finally:
        conn.close()


def query_certifications_by_partial_order(
    conn: DatabaseConnection, search_term: str, limit: int, driver: str = "sqlserver"
) -> list[Certification]:
    """Query certifications by partial order ID match.

    Args:
        conn: Database connection
        search_term: Partial order ID to search for (minimum 3 characters)
        limit: Maximum number of distinct orders to return
        driver: Database driver ('sqlserver' or 'sqlite')

    Returns:
        List of certifications matching the search term
    """
    # Select the appropriate query based on driver
    if driver == "sqlite":
        query = PARTIAL_ORDER_SEARCH_SQLITE
    else:
        query = PARTIAL_ORDER_SEARCH_SQLSERVER

    search_pattern = f"%{search_term}%"

    cursor = conn.cursor()
    cursor.execute(query, {"SearchPattern": search_pattern, "Limit": limit})
    rows = cursor.fetchall()
    cursor.close()

    # Group results by certification (same logic as query_certifications_by_order)
    certs_dict: dict[int, Certification] = {}
    seen_media: set[tuple[int, int]] = set()  # (crt_id, med_id)

    for row in rows:
        crt_id = row[4]  # crtID

        if crt_id not in certs_dict:
            certs_dict[crt_id] = Certification(
                crt_id=crt_id,
                crt_cert_no=row[0],  # crtCertNo
                crt_cust_name=row[1],  # crtCustName
                crt_cst_id=row[2],  # crt_cstID
                crt_po_number=row[3],  # crtPONumber
                crt_or_id=row[5],  # crt_orID
                media_files=[],
            )

        # Add media file if present and not already added
        med_id = row[8]  # medID
        if med_id is not None:
            key = (crt_id, med_id)
            if key not in seen_media:
                seen_media.add(key)
                media_file = MediaFile(
                    med_id=med_id,
                    med_description=row[9],  # medDescription
                    med_full_path=row[10],  # medFullPath
                    medx_id=row[7],  # medxID
                    not_id=row[6],  # notID
                )
                certs_dict[crt_id].media_files.append(media_file)

    return list(certs_dict.values())


def query_partial_order_with_customer(
    config: DatabaseConfig, search_term: str, limit: int
) -> tuple[list[Certification], Customer | None]:
    """Query certifications by partial order ID and customer info.

    Args:
        config: Database configuration
        search_term: Partial order ID to search for
        limit: Maximum number of distinct orders to return

    Returns:
        Tuple of (certifications list, customer or None)
    """
    conn = get_connection(config)
    try:
        certs = query_certifications_by_partial_order(
            conn, search_term, limit, config.driver
        )

        # Get customer from first certification
        customer = None
        if certs:
            customer = get_customer_by_id(conn, certs[0].crt_cst_id)

        return certs, customer
    finally:
        conn.close()
