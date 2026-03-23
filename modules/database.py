"""
Database initialization and utilities for SWCC QC Assistant
"""
import sqlite3
from datetime import datetime


def get_db_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str):
    """Create all required tables if they don't exist."""
    conn = get_db_connection(db_path)
    c = conn.cursor()

    # ── Master Items Table (from Excel) ──────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            item_code     TEXT UNIQUE NOT NULL,
            description   TEXT,
            quantity      REAL DEFAULT 0,
            unit          TEXT DEFAULT 'EA',
            specification TEXT,
            status        TEXT DEFAULT 'معلق',
            category      TEXT,
            supplier      TEXT,
            notes         TEXT,
            created_at    TEXT DEFAULT (datetime('now','localtime')),
            updated_at    TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── Inbound Inspection Records ────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS inbound_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            item_code       TEXT NOT NULL,
            description     TEXT,
            supplier        TEXT,
            quantity_received REAL,
            quantity_accepted REAL,
            quantity_rejected REAL,
            specification   TEXT,
            status          TEXT DEFAULT 'معلق',
            inspector       TEXT DEFAULT 'مراقب الجودة',
            inspection_date TEXT,
            location        TEXT,
            gps_lat         REAL,
            gps_lon         REAL,
            photo_path      TEXT,
            notes           TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (item_code) REFERENCES items(item_code)
        )
    """)

    # ── Shipping Records ──────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS shipping_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_no     TEXT NOT NULL,
            item_code       TEXT,
            description     TEXT,
            quantity        REAL,
            destination     TEXT,
            carrier         TEXT,
            status          TEXT DEFAULT 'جاري التحضير',
            ship_date       TEXT,
            receive_date    TEXT,
            notes           TEXT,
            photo_path      TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── RFI Records ───────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS rfi_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            rfi_no          TEXT NOT NULL,
            item_code       TEXT,
            description     TEXT,
            inspection_type TEXT,
            result          TEXT DEFAULT 'معلق',
            inspector       TEXT DEFAULT 'مراقب الجودة',
            inspection_date TEXT,
            gps_lat         REAL,
            gps_lon         REAL,
            photo_path      TEXT,
            notes           TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── Library Documents ─────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS library_docs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            file_path   TEXT NOT NULL,
            doc_type    TEXT DEFAULT 'رسم هندسي',
            item_code   TEXT,
            tags        TEXT,
            added_at    TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── Chat History ──────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            role        TEXT NOT NULL,
            message     TEXT NOT NULL,
            timestamp   TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    conn.commit()
    conn.close()


def update_item_status(db_path: str, item_code: str, status: str):
    conn = get_db_connection(db_path)
    conn.execute(
        "UPDATE items SET status=?, updated_at=? WHERE item_code=?",
        (status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item_code)
    )
    conn.commit()
    conn.close()


def search_items(db_path: str, query: str) -> list:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    like = f"%{query}%"
    c.execute("""
        SELECT item_code, description, quantity, unit, specification, status
        FROM items
        WHERE item_code LIKE ? OR description LIKE ?
        ORDER BY item_code
        LIMIT 20
    """, (like, like))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_item_by_code(db_path: str, code: str) -> dict | None:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE item_code=?", (code,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_items(db_path: str) -> list:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM items ORDER BY item_code")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows
