import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).with_name("market.db")

# Un solo file SQLite: ogni riga porta la sua `version` (uno snapshot per patch)
SCHEMA = """
CREATE TABLE IF NOT EXISTS versions (id TEXT PRIMARY KEY, label TEXT, imported_at TEXT);
CREATE TABLE IF NOT EXISTS entries  (id TEXT, version TEXT, name TEXT, type TEXT, PRIMARY KEY (id, version));
CREATE TABLE IF NOT EXISTS prices   (entry_id TEXT, version TEXT, location TEXT, buy REAL, sell REAL, stock INTEGER);
CREATE INDEX IF NOT EXISTS ix_entries_name ON entries (version, name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS ix_prices ON prices (entry_id, version);
"""


@contextmanager
def connect():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    with connect() as c:
        c.executescript(SCHEMA)
