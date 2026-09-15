"""Integration checks; run only with an explicitly configured test database."""

import os

import pytest


pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="PostgreSQL test database not configured"
)


def test_postgresql_boot_and_health():
    import web_app

    client = web_app.app.test_client()
    health = client.get("/api/health").get_json()
    assert health["ok"] is True
    assert health["database_backend"] == "postgresql"
    assert health["version"] == "V39"

    connection = web_app.con()
    assert connection.execute("SELECT COUNT(*) FROM warehouse_slots WHERE rack=1").fetchone()[0] == 356
    assert connection.execute("SELECT COUNT(*) FROM warehouse_slots WHERE rack=8").fetchone()[0] == 332
    assert connection.execute("SELECT version FROM schema_migrations WHERE version=39").fetchone()[0] == 39
    connection.close()
