"""Small transactional store for the single-host foundation release."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "dashboard.sqlite3"
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY, password_hash TEXT NOT NULL,
                    role TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    digest TEXT PRIMARY KEY, username TEXT NOT NULL,
                    csrf TEXT NOT NULL, expires REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS attempts (ip TEXT, timestamp REAL);
                CREATE TABLE IF NOT EXISTS hardware (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
                    model TEXT NOT NULL, serial TEXT NOT NULL, notes TEXT NOT NULL,
                    definition TEXT, status TEXT NOT NULL, revision INTEGER NOT NULL,
                    created_at TEXT NOT NULL, approved_by TEXT
                );
                CREATE TABLE IF NOT EXISTS captures (
                    id TEXT PRIMARY KEY, created_at TEXT NOT NULL, username TEXT NOT NULL,
                    width INTEGER, height INTEGER, sha256 TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
                    username TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL
                );
            """)
        self.path.chmod(0o600)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def audit(self, db, username, action, detail=""):
        db.execute(
            "INSERT INTO audit (created_at, username, action, detail) VALUES (?, ?, ?, ?)",
            (utc_now(), username, action, detail),
        )

    def hardware(self):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM hardware ORDER BY created_at DESC").fetchall()
        return [
            dict(row) | {"definition": json.loads(row["definition"]) if row["definition"] else None}
            for row in rows
        ]
