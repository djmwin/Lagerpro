"""One-time, non-destructive import from an old LagerPro SQLite database.

Usage:
    SQLITE_SOURCE=/path/lagerpro.db DATABASE_URL=postgresql://... python migrate_sqlite_to_postgres.py

Existing PostgreSQL rows win on conflicts; the script never deletes target data.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import psycopg
from psycopg import sql


TABLES = (
    "articles", "containers", "items", "load_carriers", "serial_numbers",
    "warehouse_slots", "movements", "inbound_checks", "tasks",
    "inventory_checks", "sage_sync_queue", "users", "audit_log",
    "slot_reservations", "app_settings", "backup_log", "stock_adjustments",
    "reorder_alerts", "email_log",
)


def main():
    source = Path(os.environ.get("SQLITE_SOURCE", ""))
    target_url = os.environ.get("DATABASE_URL", "")
    if not source.is_file() or not target_url:
        raise SystemExit("SQLITE_SOURCE (existing file) and DATABASE_URL are required")

    source_db = sqlite3.connect(source)
    source_db.row_factory = sqlite3.Row
    target = psycopg.connect(target_url)
    imported = 0
    try:
        for table in TABLES:
            exists = source_db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            if not exists:
                continue
            source_columns = [row[1] for row in source_db.execute(f"PRAGMA table_info({table})")]
            with target.cursor() as cursor:
                cursor.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position",
                    (table,),
                )
                target_columns = {row[0] for row in cursor.fetchall()}
                columns = [name for name in source_columns if name in target_columns]
                if not columns:
                    continue
                insert = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING").format(
                    sql.Identifier(table),
                    sql.SQL(",").join(map(sql.Identifier, columns)),
                    sql.SQL(",").join(sql.Placeholder() for _ in columns),
                )
                for row in source_db.execute(f"SELECT * FROM {table}"):
                    cursor.execute(insert, tuple(row[name] for name in columns))
                    imported += max(cursor.rowcount, 0)
                if "id" in columns:
                    cursor.execute(
                        sql.SQL("SELECT setval(pg_get_serial_sequence({}, 'id'), GREATEST(COALESCE(MAX(id), 1), 1), true) FROM {}").format(
                            sql.Literal(table), sql.Identifier(table)
                        )
                    )
        target.commit()
    except Exception:
        target.rollback()
        raise
    finally:
        source_db.close()
        target.close()
    print(f"Import abgeschlossen: {imported} Datensätze neu übernommen.")


if __name__ == "__main__":
    main()
