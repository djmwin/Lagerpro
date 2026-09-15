import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
db_file.close()
os.environ["LAGERPRO_DB"] = db_file.name
os.environ["LAGERPRO_SECURE_COOKIES"] = "0"
os.environ.pop("DATABASE_URL", None)

import web_app


def csrf(client):
    with client.session_transaction() as sess:
        return sess["csrf_token"]


def setup_and_login(client):
    client.get("/setup")
    response = client.post("/setup", data={
        "csrf_token": csrf(client),
        "full_name": "Test Admin",
        "username": "admin",
        "password": "secure-test-password",
    })
    assert response.status_code == 302
    client.get("/login")
    response = client.post("/login", data={
        "csrf_token": csrf(client),
        "username": "admin",
        "password": "secure-test-password",
    })
    assert response.status_code == 302


def test_health_and_warehouse_layout():
    client = web_app.app.test_client()
    health = client.get("/api/health").get_json()
    assert health == {"ok": True, "database": True, "database_backend": "sqlite", "version": "V39"}
    c = web_app.con()
    assert c.execute("SELECT COUNT(*) FROM warehouse_slots WHERE rack=1").fetchone()[0] == 356
    assert c.execute("SELECT COUNT(*) FROM warehouse_slots WHERE rack=8").fetchone()[0] == 332
    c.close()


def test_csrf_rejects_missing_token():
    client = web_app.app.test_client()
    client.get("/setup")
    assert client.post("/setup", data={"username": "x"}).status_code == 400


def test_container_completion_email_is_idempotent(monkeypatch):
    client = web_app.app.test_client()
    setup_and_login(client)
    c = web_app.con()
    c.execute("INSERT INTO containers(container_no,gate_no,status,created_at) VALUES(?,?,?,?)", ("TEST-1", 8, "angekommen", web_app.now_iso()))
    c.commit()
    cid = c.execute("SELECT id FROM containers WHERE container_no=?", ("TEST-1",)).fetchone()[0]
    c.close()
    sent = []
    monkeypatch.setattr(web_app, "send_system_email", lambda *args, **kwargs: sent.append(args) or True)
    token = csrf(client)
    assert client.post(f"/container/{cid}/finish", data={"csrf_token": token}).status_code == 302
    assert client.post(f"/container/{cid}/finish", data={"csrf_token": token}).status_code == 302
    assert len(sent) == 1


def test_admin_pages_smoke_test():
    client = web_app.app.test_client()
    client.get("/login")
    client.post("/login", data={
        "csrf_token": csrf(client),
        "username": "admin",
        "password": "secure-test-password",
    })
    routes = [
        "/", "/articles", "/containers", "/carriers", "/warehouse",
        "/gates", "/archive", "/stock", "/purchasing", "/reports",
        "/batch-booking", "/reservations", "/optimizer", "/simulation",
        "/handover", "/notifications", "/audit", "/backup", "/settings",
        "/users", "/email-log", "/tasks", "/inventory", "/quality",
    ]
    for route in routes:
        response = client.get(route)
        assert response.status_code < 500, (route, response.status_code)


def test_security_headers_and_cookie_policy():
    client = web_app.app.test_client()
    response = client.get("/api/health", base_url="https://lagerpro.example")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["Strict-Transport-Security"].startswith("max-age=")
    cookie = response.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_role_boundaries_and_state_changes_require_post():
    client = web_app.app.test_client()
    client.get("/login")
    with client.session_transaction() as sess:
        sess.update(user_id=999, username="worker", role="Mitarbeiter", csrf_token="test-token")
    assert client.get("/purchasing").status_code == 403
    assert client.get("/task/1/done").status_code == 405
    assert client.get("/logout").status_code == 405


def test_markup_in_request_is_rejected():
    client = web_app.app.test_client()
    assert client.get("/search?q=%3Cscript%3Ebad%3C/script%3E").status_code == 400
