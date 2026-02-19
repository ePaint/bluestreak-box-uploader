"""Seed SQLite database with sample data for testing."""

import sqlite3
from pathlib import Path


SCHEMA = """
-- Certification table
CREATE TABLE IF NOT EXISTS Certification (
    crtID INTEGER PRIMARY KEY AUTOINCREMENT,
    crtCertNo VARCHAR(25) NOT NULL,
    crtDate DATETIME NOT NULL,
    crtVersion SMALLINT NOT NULL DEFAULT 1,
    crt_cstID INTEGER NOT NULL,
    crt_orID INTEGER NOT NULL,
    crtPONumber VARCHAR(25),
    crtCustName VARCHAR(100) NOT NULL,
    crtAddress1 VARCHAR(100) NOT NULL,
    crtAddress2 VARCHAR(100),
    crtAddress3 VARCHAR(100),
    crtCity VARCHAR(50) NOT NULL,
    crtStateProvince VARCHAR(50) NOT NULL,
    crtPostalCode VARCHAR(10) NOT NULL
);

-- Customer table
CREATE TABLE IF NOT EXISTS Customer (
    cstID INTEGER PRIMARY KEY AUTOINCREMENT,
    cstName VARCHAR(100) NOT NULL,
    cstListName VARCHAR(100) NOT NULL,
    cstIntegrationID VARCHAR(50),
    cstIsActive BIT NOT NULL DEFAULT 1
);

-- Note table
CREATE TABLE IF NOT EXISTS Note (
    notID INTEGER PRIMARY KEY AUTOINCREMENT,
    not_crtID INTEGER,
    notDate DATETIME NOT NULL,
    notSubject VARCHAR(750),
    notBody TEXT NOT NULL,
    FOREIGN KEY (not_crtID) REFERENCES Certification(crtID)
);

-- Media table
CREATE TABLE IF NOT EXISTS Media (
    medID INTEGER PRIMARY KEY AUTOINCREMENT,
    medDescription VARCHAR(250) NOT NULL,
    medFullPath VARCHAR(500) NOT NULL,
    medIsActive BIT NOT NULL DEFAULT 1
);

-- MediaXref table
CREATE TABLE IF NOT EXISTS MediaXref (
    medxID INTEGER PRIMARY KEY AUTOINCREMENT,
    medx_medID INTEGER,
    medx_crtID INTEGER,
    medx_notID INTEGER,
    medxDeletedDate DATETIME,
    FOREIGN KEY (medx_medID) REFERENCES Media(medID),
    FOREIGN KEY (medx_crtID) REFERENCES Certification(crtID),
    FOREIGN KEY (medx_notID) REFERENCES Note(notID)
);
"""


def seed_database(db_path: str | Path) -> None:
    """Create and seed the SQLite database with sample data."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create schema
    cursor.executescript(SCHEMA)

    # Clear existing data
    cursor.execute("DELETE FROM MediaXref")
    cursor.execute("DELETE FROM Media")
    cursor.execute("DELETE FROM Note")
    cursor.execute("DELETE FROM Certification")
    cursor.execute("DELETE FROM Customer")

    # Insert customer - Burton Industries (cstID=1916, with Box integration)
    cursor.execute("""
        INSERT INTO Customer (cstID, cstName, cstListName, cstIntegrationID, cstIsActive)
        VALUES (1916, 'Burton Industries Inc.', 'Burton Industries', NULL, 1)
    """)

    # Insert customer without Box integration for testing warnings
    cursor.execute("""
        INSERT INTO Customer (cstID, cstName, cstListName, cstIntegrationID, cstIsActive)
        VALUES (825, 'H & H Swiss', 'H & H Swiss', NULL, 1)
    """)

    # Sample data from the CSV - Order 444337
    certs_data = [
        # (crtID, crtCertNo, crt_cstID, crt_orID, crtPONumber, crtCustName, city, state, zip)
        (1, "444337-1", 1916, 444337, "123456TEST", "Burton Industries Inc.", "West Babylon", "NY", "11704"),
        (2, "444337-1-1", 1916, 444337, "123456TEST", "Burton Industries Inc.", "West Babylon", "NY", "11704"),
        (3, "444337-2", 1916, 444337, "123456TEST", "Burton Industries Inc.", "West Babylon", "NY", "11704"),
        (4, "444337-2-1", 1916, 444337, "123456TEST", "Burton Industries Inc.", "West Babylon", "NY", "11704"),
        (5, "444337-2-2", 1916, 444337, "123456TEST", "Burton Industries Inc.", "West Babylon", "NY", "11704"),
        (6, "444337-2-3", 1916, 444337, "123456TEST", "Burton Industries Inc.", "West Babylon", "NY", "11704"),
    ]

    for crt in certs_data:
        cursor.execute("""
            INSERT INTO Certification (crtID, crtCertNo, crtDate, crt_cstID, crt_orID, crtPONumber,
                                       crtCustName, crtAddress1, crtCity, crtStateProvince, crtPostalCode)
            VALUES (?, ?, datetime('now'), ?, ?, ?, ?, '243 Wyandanch Ave', ?, ?, ?)
        """, crt)

    # Insert notes for certifications (one per cert for media linking)
    notes_data = [
        (1, 1, "Approved Certification"),
        (2, 2, "Approved Certification"),
        (3, 2, "Hardness Chart"),
        (4, 3, "Approved Certification"),
        (5, 3, "Nadcap"),
        (6, 4, "Approved Certification"),
        (7, 4, "Bollard-Guard-Cover-Spec-Sheet"),
        (8, 5, "Approved Certification"),
        (9, 5, "353.jpg"),
        (10, 5, "pmt-hps-trendview"),
        (11, 6, "Approved Certification"),
        (12, 6, "Field-Instruments"),
        (13, 6, "pmt-hps-43-tv-07-46"),
        (14, 6, "pmt-hps-43-tv-33-56"),
    ]

    for note in notes_data:
        cursor.execute("""
            INSERT INTO Note (notID, not_crtID, notDate, notSubject, notBody)
            VALUES (?, ?, datetime('now'), ?, 'Note body')
        """, note)

    # Insert media files
    media_data = [
        (1, "Approved Certification Kamil Siniakowicz - 2/19/2026 12:09 PM", "202602/ApprovedCert_444337-1_263756.pdf"),
        (2, "Approved Certification Kamil Siniakowicz - 2/19/2026 12:09 PM", "202602/ApprovedCert_444337-1-1_263757.pdf"),
        (3, "Hardness Chart.pdf added by kamil on 2/19/2026 12:11 PM", "202602/Hardness_Chart_263761.pdf"),
        (4, "Approved Certification Kamil Siniakowicz - 2/19/2026 12:09 PM", "202602/ApprovedCert_444337-2_263758.pdf"),
        (5, "Nadcap.pdf added by kamil on 2/19/2026 12:12 PM", "202602/Nadcap_263762.pdf"),
        (6, "Approved Certification Kamil Siniakowicz - 2/19/2026 12:09 PM", "202602/ApprovedCert_444337-2-1_263759.pdf"),
        (7, "Bollard-Guard-Cover-Spec-Sheet.pdf added by kamil on 2/19/2026 12:14 PM", "202602/Bollard-Guard-Cover-Spec-Sheet_263763.pdf"),
        (8, "Approved Certification Kamil Siniakowicz - 2/19/2026 12:10 PM", "202602/ApprovedCert_444337-2-2_263760.pdf"),
        (9, "353.jpg added by kamil on 2/19/2026 12:15 PM", "202602/353_263765.jpg"),
        (10, "pmt-hps-trendview-r220-4-02-dep-scn (3).pdf added by kamil on 2/19/2026 12:18 PM", "202602/pmt-hps-trendview-r220-4-02-dep-scn_(3)_263766.pdf"),
        (11, "Approved Certification Kamil Siniakowicz - 2/19/2026 12:18 PM", "202602/ApprovedCert_444337-2-3_263767.pdf"),
        (12, "Field-Instruments-and-Control-Solutions-Catalogue.pdf added by kamil on 2/19/2026 12:19 PM", "202602/Field-Instruments-and-Control-Solutions-Catalogue_263768.pdf"),
        (13, "pmt-hps-43-tv-07-46-en-tvrecorder-tms-dcom-settings-historian-server-appnotes-issue2.pdf added by kamil on 2/19/2026 12:19 PM", "202602/pmt-hps-43-tv-07-46-en-tvrecorder-tms-dcom-settings-historian-server-appnotes-issue2_263769.pdf"),
        (14, "pmt-hps-43-tv-33-56.pdf added by kamil on 2/19/2026 12:19 PM", "202602/pmt-hps-43-tv-33-56_263770.pdf"),
    ]

    for media in media_data:
        cursor.execute("""
            INSERT INTO Media (medID, medDescription, medFullPath, medIsActive)
            VALUES (?, ?, ?, 1)
        """, media)

    # Link media to notes/certs via MediaXref
    # Format: (medxID, medx_medID, medx_crtID, medx_notID)
    # Cert 1 (444337-1): 1 file
    # Cert 2 (444337-1-1): 2 files
    # Cert 3 (444337-2): 2 files
    # Cert 4 (444337-2-1): 2 files
    # Cert 5 (444337-2-2): 3 files
    # Cert 6 (444337-2-3): 4 files
    xref_data = [
        (1, 1, 1, 1),    # Cert 1, media 1, note 1
        (2, 2, 2, 2),    # Cert 2, media 2, note 2
        (3, 3, 2, 3),    # Cert 2, media 3, note 3
        (4, 4, 3, 4),    # Cert 3, media 4, note 4
        (5, 5, 3, 5),    # Cert 3, media 5, note 5
        (6, 6, 4, 6),    # Cert 4, media 6, note 6
        (7, 7, 4, 7),    # Cert 4, media 7, note 7
        (8, 8, 5, 8),    # Cert 5, media 8, note 8
        (9, 9, 5, 9),    # Cert 5, media 9, note 9
        (10, 10, 5, 10), # Cert 5, media 10, note 10
        (11, 11, 6, 11), # Cert 6, media 11, note 11
        (12, 12, 6, 12), # Cert 6, media 12, note 12
        (13, 13, 6, 13), # Cert 6, media 13, note 13
        (14, 14, 6, 14), # Cert 6, media 14, note 14
    ]

    for xref in xref_data:
        cursor.execute("""
            INSERT INTO MediaXref (medxID, medx_medID, medx_crtID, medx_notID)
            VALUES (?, ?, ?, ?)
        """, xref)

    conn.commit()
    conn.close()

    print(f"Database seeded: {db_path}")
    print("  - 2 customers (Burton Industries, H & H Swiss)")
    print("  - 6 certifications for order 444337")
    print("  - 14 media files")


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "test.db"
    seed_database(db_path)
