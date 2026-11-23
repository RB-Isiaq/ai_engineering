"""SQLite persistence for the travel desk: routes out of Lagos and customer bookings."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).with_name("travel_desk.db")

ROUTES = [
    # city, country, economy, business, flight hours
    ("accra", "Ghana", 180, 520, 1.2),
    ("nairobi", "Kenya", 540, 1450, 5.0),
    ("johannesburg", "South Africa", 690, 1900, 6.0),
    ("london", "United Kingdom", 820, 3100, 6.5),
    ("paris", "France", 790, 2950, 6.3),
    ("dubai", "United Arab Emirates", 610, 2400, 7.0),
    ("new york", "United States", 1150, 4200, 11.5),
    ("toronto", "Canada", 1240, 4350, 13.0),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS routes (
    city TEXT PRIMARY KEY,
    country TEXT NOT NULL,
    fare_economy REAL NOT NULL,
    fare_business REAL NOT NULL,
    flight_hours REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS bookings (
    reference TEXT PRIMARY KEY,
    passenger TEXT NOT NULL,
    city TEXT NOT NULL REFERENCES routes(city),
    cabin TEXT NOT NULL,
    travel_date TEXT NOT NULL,
    price REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'confirmed',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT OR IGNORE INTO routes VALUES (?, ?, ?, ?, ?)", ROUTES)
