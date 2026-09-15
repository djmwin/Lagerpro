"""Small DB-API compatibility layer for SQLite and Railway PostgreSQL.

The legacy application uses SQLite-style qmark parameters.  Keeping that API
here lets the existing warehouse workflows run against PostgreSQL while the
application is split into modules over time.
"""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path


DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
SQLITE_PATH = os.environ.get(
    "LAGERPRO_DB", str(Path(__file__).with_name("lagerpro.db"))
)
BACKEND = "postgresql" if DATABASE_URL else "sqlite"


class Row(dict):
    """Mapping row that also supports SQLite's integer indexing."""

    def __init__(self, values=(), columns=()):
        super().__init__(zip(columns, values))
        self._values = tuple(values)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)


class Cursor:
    def __init__(self, cursor, buffered=None, lastrowid=None):
        self._cursor = cursor
        self._buffered = list(buffered or [])
        self.lastrowid = lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def _row(self, raw):
        if raw is None:
            return None
        if isinstance(raw, sqlite3.Row):
            return raw
        if isinstance(raw, dict):
            return Row(raw.values(), raw.keys())
        columns = [x.name if hasattr(x, "name") else x[0] for x in self._cursor.description]
        return Row(raw, columns)

    def fetchone(self):
        if self._buffered:
            return self._buffered.pop(0)
        return self._row(self._cursor.fetchone())

    def fetchall(self):
        rows = self._buffered
        self._buffered = []
        rows.extend(self._row(x) for x in self._cursor.fetchall())
        return rows


IDENTITY_TABLES = {
    "articles", "containers", "items", "warehouse_slots", "load_carriers",
    "serial_numbers", "movements", "inbound_checks", "tasks",
    "inventory_checks", "sage_sync_queue", "users", "audit_log",
    "slot_reservations", "backup_log", "stock_adjustments", "reorder_alerts",
    "email_log",
}


def _postgres_sql(sql):
    sql = sql.strip()
    sql = re.sub(r"\bINTEGER PRIMARY KEY AUTOINCREMENT\b", "BIGSERIAL PRIMARY KEY", sql, flags=re.I)
    sql = re.sub(r"\bINSERT\s+OR\s+IGNORE\s+INTO\b", "INSERT INTO", sql, flags=re.I)
    if re.match(r"INSERT\s+INTO\s+warehouse_slots\b", sql, re.I) and "ON CONFLICT" not in sql.upper():
        sql += " ON CONFLICT (rack, level, position) DO NOTHING"
    # The app only uses GROUP_CONCAT for human-readable slot lists.
    sql = re.sub(
        r"GROUP_CONCAT\((rack\|\|'-'\|\|level\|\|'-'\|\|position)\)",
        r"STRING_AGG(CAST(\1 AS TEXT), ',')",
        sql,
        flags=re.I,
    )
    return sql.replace("?", "%s")


class Connection:
    def __init__(self):
        self.backend = BACKEND
        if BACKEND == "sqlite":
            self._connection = sqlite3.connect(SQLITE_PATH, timeout=30)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys=ON")
            self._connection.execute("PRAGMA busy_timeout=30000")
        else:
            import psycopg

            self._connection = psycopg.connect(DATABASE_URL, connect_timeout=10)

    def execute(self, sql, params=()):
        if self.backend == "sqlite":
            return self._connection.execute(sql, params)

        pragma = re.fullmatch(r"\s*PRAGMA\s+table_info\((\w+)\)\s*", sql, re.I)
        cursor = self._connection.cursor()
        if pragma:
            cursor.execute(
                "SELECT ordinal_position - 1 AS cid, column_name AS name "
                "FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position",
                (pragma.group(1),),
            )
            return Cursor(cursor)

        translated = _postgres_sql(sql)
        identity = re.match(r"\s*INSERT\s+(?:OR\s+IGNORE\s+)?INTO\s+(\w+)", sql, re.I)
        wants_id = (
            identity
            and identity.group(1).lower() in IDENTITY_TABLES
            and "RETURNING" not in translated.upper()
            and "ON CONFLICT" not in translated.upper()
        )
        if wants_id:
            translated += " RETURNING id"
        cursor.execute(translated, tuple(params or ()))
        lastrowid = None
        buffered = []
        if wants_id:
            raw = cursor.fetchone()
            if raw:
                lastrowid = raw[0]
        return Cursor(cursor, buffered=buffered, lastrowid=lastrowid)

    def executescript(self, script):
        if self.backend == "sqlite":
            return self._connection.executescript(script)
        for statement in script.split(";"):
            if statement.strip():
                self.execute(statement)

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()


def connect():
    return Connection()


def database_backend():
    return BACKEND
