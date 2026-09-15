# LagerPro V39 - PostgreSQL, Sicherheit und stabile Lagerbuchungen
from flask import Flask, request, redirect, session, abort, g
import os, math, json, shutil, secrets, smtplib, ssl, hmac
import re
import logging
import sqlite3
from psycopg import IntegrityError as PostgresIntegrityError
from email.message import EmailMessage
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from markupsafe import escape
from database import connect as database_connect, database_backend

INTEGRITY_ERRORS = (sqlite3.IntegrityError, PostgresIntegrityError)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
if os.environ.get("DATABASE_URL") and not os.environ.get("LAGERPRO_SECRET"):
    raise RuntimeError("LAGERPRO_SECRET muss im Produktionsbetrieb gesetzt sein")
app.secret_key = os.environ.get("LAGERPRO_SECRET") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("LAGERPRO_SECURE_COOKIES", "1") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
)
DB = os.environ.get("LAGERPRO_DB", os.path.join(os.path.dirname(__file__), "lagerpro.db"))
LOGO_DATA = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAb8AAAG/CAMAAAD/zSlAAAAA8FBMVEX///8lHUL8vRr///0AAAC6uL+KiZAlHUQAACQnH0UAABqqqbOoprL7uw/2xUYAACb49/kfFj4AAAj99dr///jg3+Tzx1EXDDrw8PIAACAAAB3Y1tsAACsmIj+/vsMOADH889Fyb4BxcHrOy9J6eoT2wDhTUGELADUaGS84M07utxj++s1kYnD40noAABb52YlERFKdmqQTEyQSCDH+/dj//e1APlEAADD57LxPTllaWGNOTlKIhpQZFTEXEjQuLEPt6vUkIzNBQEX235XuxVxgYGM2NkH34qQqKjIPDhj21HAhIR9RS2RcWXJFP1ogHyQnirSlAAAgAElEQVR4nO2dC3vaOLOATQ0I42SxSVyb4OAGU2i6lC8sG2jYXJpe0p492/3+/785GskG2xpjQ0jTPmfep9uy4IussUaj0WikaQRBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEDujP3cBCILIQs3y14bk90ugWw6G99zlIkrSq7YUGh+d5y4WUZL+gim4g+cuFVESq80qCq3ecxeLKIWu9dqq+FjH0sl8+RXQtStbld9oqZH8fgV0zfnGmJERnzGpPXfBiFLomnmb6f74/9o3Ho3+fhHqbrbvq1QWZ6Q+fwm4+lzaUmZJAZ7UuPxIgL8CZqBaL+6QBu+/CFbdV+W3qFvPXS6iHM4dMnqYmc9dLKIMvIfjg3fF+2LPw+cuGVEKXesvsmM/3v19ee5yEaXQdevGVuXH1SfZnr8AfIQQVlX1yf6gwfsvAZdff4SMHpbPXTCiFLrm/VedOjLaNXK+/CwIL0rkSkFkYt4yo5LpAFnVIvn9LIDo9OgvRIL9rO+Ti282fI6CEiibG5JzoQ7ejQkN3n8aLMvznF7tYDo1a6HnZb1iNVvt/uybX8L3aUn2eMWfpc+I9aTldM3B+K5Zrbab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"

def con():
    return database_connect()

def calc(q, cpp):
    q = int(q)
    cpp = max(1, int(cpp))
    return q // cpp, q % cpp, math.ceil(q / cpp) if q else 0

def init_db():
    c = con()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS articles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        pallet_type TEXT NOT NULL DEFAULT 'Euro',
        cpp INTEGER NOT NULL DEFAULT 1,
        storage_rule TEXT NOT NULL DEFAULT 'Alle Ebenen'
    );

    CREATE TABLE IF NOT EXISTS containers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_no TEXT NOT NULL,
        gate_no INTEGER,
        status TEXT NOT NULL DEFAULT 'geplant',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_id INTEGER NOT NULL,
        article_no TEXT NOT NULL,
        name TEXT NOT NULL,
        cartons INTEGER NOT NULL,
        cpp INTEGER NOT NULL,
        pallet_type TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS warehouse_slots(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rack INTEGER NOT NULL,
        level INTEGER NOT NULL,
        position INTEGER NOT NULL,
        article_no TEXT,
        article_name TEXT,
        pallet_type TEXT,
        quantity INTEGER,
        container_id INTEGER,
        occupied_at TEXT,
        UNIQUE(rack, level, position)
    );
    """)

    for rack in range(1, 31):
        for level in range(1, 5):
            for position in range(1, 84):
                c.execute(
                    """INSERT OR IGNORE INTO warehouse_slots(rack,level,position)
                       VALUES(?,?,?)""",
                    (rack, level, position)
                )

    # V17: real warehouse flow: cartons -> pieces -> load carrier -> serials -> storage slot
    def add_col(table, definition):
        name = definition.split()[0]
        cols = {r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()}
        if name not in cols:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")

    # V24: Kompatibilitaet mit alten Railway-Datenbanken.
    # Aeltere Versionen verwenden "name", neuere Funktionen "article_name".
    # Wir behalten beide Felder und synchronisieren vorhandene Werte.
    add_col("articles", "article_name TEXT")
    add_col("articles", "units_per_carton INTEGER NOT NULL DEFAULT 1")
    add_col("articles", "min_stock INTEGER NOT NULL DEFAULT 0")
    add_col("articles", "target_stock INTEGER NOT NULL DEFAULT 0")
    c.execute("""
        UPDATE articles
        SET article_name = COALESCE(NULLIF(article_name,''), name)
        WHERE article_name IS NULL OR article_name=''
    """)
    c.execute("""
        UPDATE articles
        SET name = COALESCE(NULLIF(name,''), article_name, article_no)
        WHERE name IS NULL OR name=''
    """)
    add_col("items", "units_per_carton INTEGER NOT NULL DEFAULT 1")
    add_col("items", "article_count INTEGER NOT NULL DEFAULT 0")
    add_col("warehouse_slots", "load_carrier_no TEXT")
    add_col("warehouse_slots", "load_carrier_id INTEGER")

    c.executescript("""
    CREATE TABLE IF NOT EXISTS load_carriers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        carrier_no TEXT NOT NULL UNIQUE,
        container_id INTEGER,
        article_no TEXT,
        article_name TEXT,
        quantity INTEGER NOT NULL DEFAULT 0,
        pallet_type TEXT,
        status TEXT NOT NULL DEFAULT 'offen',
        rack INTEGER,
        level INTEGER,
        position INTEGER,
        created_at TEXT NOT NULL,
        closed_at TEXT,
        stored_at TEXT
    );

    CREATE TABLE IF NOT EXISTS serial_numbers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        load_carrier_id INTEGER NOT NULL,
        serial_no TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS movements(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        load_carrier_id INTEGER,
        carrier_no TEXT,
        movement_type TEXT NOT NULL,
        from_slot TEXT,
        to_slot TEXT,
        created_at TEXT NOT NULL
    );
    """)
    add_col("movements", "article_no TEXT")
    add_col("movements", "quantity INTEGER NOT NULL DEFAULT 0")

    # Backfill article_count for old container positions if present.
    c.execute("""
        UPDATE items
        SET article_count = cartons * COALESCE(NULLIF(units_per_carton,0),1)
        WHERE COALESCE(article_count,0)=0
    """)

    # V18: Leitstand, Qualität, Sperrplätze, Aufträge, Inventur und Sage-Sync-Vorbereitung
    add_col("warehouse_slots", "slot_status TEXT NOT NULL DEFAULT 'frei'")
    add_col("warehouse_slots", "block_reason TEXT")
    add_col("warehouse_slots", "capacity INTEGER NOT NULL DEFAULT 4")
    c.execute("UPDATE warehouse_slots SET capacity=CASE WHEN position IN (21,22,23) THEN 3 ELSE 4 END")
    add_col("load_carriers", "quality_status TEXT NOT NULL DEFAULT 'frei'")
    add_col("load_carriers", "quality_note TEXT")
    add_col("containers", "planned_arrival TEXT")
    add_col("containers", "arrival_at TEXT")
    add_col("containers", "unload_started_at TEXT")
    add_col("containers", "unload_finished_at TEXT")
    add_col("containers", "departed_at TEXT")
    add_col("containers", "carrier_name TEXT")
    add_col("containers", "truck_plate TEXT")
    add_col("containers", "seal_no TEXT")
    add_col("containers", "delivery_note TEXT")
    add_col("containers", "issue_note TEXT")
    add_col("containers", "completion_email_claimed_at TEXT")
    add_col("containers", "completion_email_sent_at TEXT")
    add_col("containers", "completion_email_error TEXT")

    c.executescript("""
    CREATE TABLE IF NOT EXISTS inbound_checks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_id INTEGER NOT NULL,
        article_no TEXT NOT NULL,
        expected_cartons INTEGER NOT NULL DEFAULT 0,
        received_cartons INTEGER NOT NULL DEFAULT 0,
        damaged_units INTEGER NOT NULL DEFAULT 0,
        missing_units INTEGER NOT NULL DEFAULT 0,
        note TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        task_type TEXT NOT NULL DEFAULT 'Allgemein',
        priority TEXT NOT NULL DEFAULT 'Normal',
        carrier_no TEXT,
        from_slot TEXT,
        to_slot TEXT,
        note TEXT,
        status TEXT NOT NULL DEFAULT 'offen',
        created_at TEXT NOT NULL,
        completed_at TEXT
    );

    CREATE TABLE IF NOT EXISTS inventory_checks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_code TEXT NOT NULL,
        expected_carrier TEXT,
        scanned_carrier TEXT,
        result TEXT NOT NULL,
        note TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sage_sync_queue(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        action TEXT NOT NULL,
        payload TEXT,
        status TEXT NOT NULL DEFAULT 'wartet',
        error_text TEXT,
        created_at TEXT NOT NULL,
        synced_at TEXT
    );
    """)

    c.execute("""
        UPDATE warehouse_slots
        SET slot_status = CASE
            WHEN COALESCE(slot_status,'')='gesperrt' THEN 'gesperrt'
            WHEN load_carrier_id IS NOT NULL THEN 'belegt'
            ELSE 'frei'
        END
    """)


    # V30 complete extensions
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,full_name TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'Mitarbeiter',active INTEGER NOT NULL DEFAULT 1,failed_logins INTEGER NOT NULL DEFAULT 0,locked_until TEXT,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,username TEXT,action TEXT NOT NULL,entity_type TEXT,entity_id TEXT,before_json TEXT,after_json TEXT,note TEXT,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS slot_reservations(id INTEGER PRIMARY KEY AUTOINCREMENT,slot_code TEXT NOT NULL,article_no TEXT,container_id INTEGER,reason TEXT,status TEXT NOT NULL DEFAULT 'aktiv',reserved_by TEXT,created_at TEXT NOT NULL,expires_at TEXT);
    CREATE TABLE IF NOT EXISTS app_settings(setting_key TEXT PRIMARY KEY,setting_value TEXT,updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS backup_log(id INTEGER PRIMARY KEY AUTOINCREMENT,filename TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS stock_adjustments(id INTEGER PRIMARY KEY AUTOINCREMENT,carrier_id INTEGER,old_quantity INTEGER,new_quantity INTEGER,reason TEXT NOT NULL,requested_by TEXT,approved_by TEXT,status TEXT NOT NULL DEFAULT 'freigegeben',created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS reorder_alerts(id INTEGER PRIMARY KEY AUTOINCREMENT,article_no TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'offen',stock_at_alert INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,closed_at TEXT,email_sent_at TEXT);
    CREATE TABLE IF NOT EXISTS email_log(id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT NOT NULL,recipient TEXT,subject TEXT,status TEXT NOT NULL,error_text TEXT,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY,applied_at TEXT NOT NULL);
    """)
    add_col("reorder_alerts", "email_attempts INTEGER NOT NULL DEFAULT 0")
    add_col("reorder_alerts", "last_email_attempt_at TEXT")
    c.executescript("""
    CREATE INDEX IF NOT EXISTS idx_slots_state ON warehouse_slots(slot_status,load_carrier_id);
    CREATE INDEX IF NOT EXISTS idx_carriers_article_status ON load_carriers(article_no,status);
    CREATE INDEX IF NOT EXISTS idx_movements_created ON movements(created_at);
    CREATE INDEX IF NOT EXISTS idx_containers_status_gate ON containers(status,gate_no);
    CREATE INDEX IF NOT EXISTS idx_reorders_article_status ON reorder_alerts(article_no,status);
    """)
    # Gang 1-7: 89 Positionen. Position 21-23: 3er statt 4er.
    for gang in range(1,8):
        for level in range(1,5):
            for position in range(84,90):
                c.execute("INSERT OR IGNORE INTO warehouse_slots(rack,level,position,capacity) VALUES(?,?,?,4)",(gang,level,position))
    c.execute("UPDATE warehouse_slots SET capacity=CASE WHEN position IN (21,22,23) THEN 3 ELSE 4 END")
    c.execute("INSERT INTO schema_migrations(version,applied_at) VALUES(39,?) ON CONFLICT(version) DO NOTHING",(datetime.now().isoformat(timespec="seconds"),))
    c.commit()
    c.close()

STYLE = """
<style>
:root{
  --bg:#07111f;
  --panel:#0d1b2d;
  --panel2:#11233a;
  --border:#203a5b;
  --text:#f6f8fc;
  --muted:#9cafc8;
  --yellow:#ffcc00;
  --green:#35e27a;
  --red:#ff4b4b;
  --blue:#8eadd7;
}
*{box-sizing:border-box}
html,body{
  margin:0;
  min-height:100%;
  background:
    radial-gradient(circle at top right,#102847 0,transparent 35%),
    linear-gradient(180deg,#07111f,#071523 60%,#06101c);
  color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif
}
body{padding-bottom:92px}
body.auth-only{padding-bottom:0}
body.auth-only .main{max-width:520px;margin:40px auto;padding:16px}
body.auth-only .card{box-shadow:0 20px 60px rgba(0,0,0,.28)}
.topbar{
  position:sticky;top:0;z-index:100;
  background:rgba(6,17,29,.97);
  border-bottom:1px solid #19304d;
  backdrop-filter:blur(18px)
}
.top-inner{
  max-width:1200px;margin:auto;padding:12px 16px;
  display:flex;align-items:center;justify-content:space-between
}
.logo-wrap{
  background:white;border-radius:14px;padding:7px 10px;
  display:inline-flex;align-items:center
}
.logo-wrap img{height:58px;width:auto;display:block}
.profile{display:flex;gap:10px;align-items:center}
.avatar{
  width:44px;height:44px;border-radius:50%;
  display:grid;place-items:center;background:#233a5c;
  border:1px solid #5877a5;font-weight:800
}
.datetime{font-size:12px;color:var(--muted);text-align:right}
.main{max-width:1200px;margin:auto;padding:14px}
.hero{
  position:relative;overflow:hidden;min-height:180px;
  border:1px solid var(--border);border-radius:18px;
  display:flex;align-items:center;padding:24px;
  background:linear-gradient(90deg,rgba(5,15,28,.98),rgba(11,33,57,.94),rgba(11,33,57,.72))
}
.hero:after{
  content:"";position:absolute;right:-80px;top:-90px;width:430px;height:380px;
  background:
    linear-gradient(120deg,transparent 46%,var(--yellow) 47%,var(--yellow) 50%,transparent 51%),
    repeating-linear-gradient(90deg,rgba(255,204,0,.08) 0 32px,transparent 32px 67px);
  transform:skewX(-14deg)
}
.hero-content{position:relative;z-index:2}
.hero-small{letter-spacing:4px;color:#b7c8e0;font-size:14px}
.hero h1{margin:5px 0 10px;font-size:44px;line-height:1}
.hero p{margin:0;color:#b7c7dc;font-size:17px}
.cards{
  display:grid;grid-template-columns:repeat(4,1fr);
  gap:12px;margin-top:12px
}
.card{
  border:1px solid var(--border);border-radius:18px;padding:17px;
  background:linear-gradient(145deg,var(--panel),var(--panel2));
  box-shadow:0 20px 45px rgba(0,0,0,.18);
  margin-top:12px
}
.card-title{color:#b7c7dc;font-weight:700;font-size:14px}
.number{font-size:38px;font-weight:850;margin:5px 0}
.muted{color:var(--muted)}
.progress{
  height:10px;border-radius:30px;background:#263d5b;
  overflow:hidden;margin-top:11px
}
.progress span{display:block;height:100%;background:var(--green);border-radius:30px}
.section-head{
  display:flex;align-items:center;justify-content:space-between;
  margin-bottom:13px
}
.section-head h2{margin:0;font-size:20px}
.yellow-link{color:var(--yellow);text-decoration:none;font-weight:800}
.gates{
  display:grid;grid-template-columns:repeat(5,1fr);gap:9px
}
.gate{
  background:#091728;border:1px solid #223c5d;
  border-radius:15px;padding:15px;text-align:center
}
.gate-number{font-weight:800}
.dot{
  width:21px;height:21px;display:inline-block;
  border-radius:50%;margin:9px 0
}
.green{background:var(--green)}
.red{background:var(--red)}
.yellow-dot{background:var(--yellow)}
.gray{background:#60799e}
.status-green{color:var(--green);font-weight:800}
.status-red{color:var(--red);font-weight:800}
.status-yellow{color:var(--yellow);font-weight:800}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.donut-wrap{display:flex;align-items:center;gap:20px;flex-wrap:wrap}
.donut{
  width:155px;height:155px;border-radius:50%;
  display:grid;place-items:center
}
.donut-inner{
  width:95px;height:95px;border-radius:50%;
  background:#091726;display:grid;place-items:center;text-align:center
}
.donut-number{font-size:27px;font-weight:900}
input,select{
  width:100%;padding:12px;margin:6px 0 12px;
  border-radius:11px;border:1px solid #294766;
  background:#071423;color:white
}
button,.button{
  display:inline-block;padding:11px 15px;border:0;border-radius:11px;
  background:var(--yellow);color:#06111e;text-decoration:none;font-weight:900
}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
table{width:100%;border-collapse:collapse}
th,td{
  padding:11px 8px;text-align:left;
  border-bottom:1px solid #203650
}
th{color:#aebed3}
.badge{
  display:inline-block;padding:5px 9px;border-radius:20px;
  background:#213652
}
.kicker{
  color:var(--yellow);font-size:12px;letter-spacing:2px;font-weight:900
}
.page-title{margin:7px 0 15px;font-size:30px}
.bottom-nav{
  position:fixed;left:0;right:0;bottom:0;z-index:200;
  overflow-x:auto;
  background:rgba(6,17,29,.98);border-top:1px solid #1d3655;
  display:flex;justify-content:space-around;padding:7px 3px 11px
}
.bottom-nav a{
  min-width:65px;padding:5px 2px;color:#9eb2cf;
  text-align:center;text-decoration:none;font-size:12px
}
.bottom-nav .icon{display:block;font-size:22px;margin-bottom:3px}
.bottom-nav a.active{
  color:var(--yellow);border-bottom:3px solid var(--yellow)
}

.warehouse-toolbar{
  display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px
}
.slot-grid{
  display:grid;grid-template-columns:repeat(12,minmax(74px,1fr));
  gap:7px;overflow-x:auto;padding-bottom:5px
}
.slot{
  min-height:76px;border:1px solid #294766;border-radius:12px;
  padding:8px;background:#0a1727;color:white;text-decoration:none;
  display:flex;flex-direction:column;justify-content:space-between
}
.slot.free{border-color:#28415f;background:#091522}
.slot.occupied{border-color:#2f8f59;background:#0b271b}
.slot .slot-code{font-weight:900;font-size:13px}
.slot .slot-info{font-size:11px;color:#c2d0e2;line-height:1.2}
.slot .slot-state{font-size:10px;font-weight:900;letter-spacing:.5px}
.slot.free .slot-state{color:#7f94af}
.slot.occupied .slot-state{color:var(--green)}

.scanbox{
  border:1px solid #36577c;background:#091827;border-radius:16px;padding:14px;margin:12px 0
}
.scan-input{
  font-size:20px!important;font-weight:800;letter-spacing:.4px;
  min-height:52px!important;border:2px solid #36577c!important
}
.progress{
  height:12px;background:#07111f;border:1px solid #294766;border-radius:999px;overflow:hidden;margin:8px 0
}
.progress > span{display:block;height:100%;background:var(--yellow);border-radius:999px}
.action-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.action-card{
  display:block;text-decoration:none;color:white;background:#0d1b2d;border:1px solid #203a5b;
  border-radius:16px;padding:16px
}
.action-card b{display:block;font-size:18px;margin-bottom:5px}
.ok{color:var(--green)} .warn{color:var(--yellow)} .danger{color:var(--red)}
@media(max-width:760px){.action-grid{grid-template-columns:1fr}.scan-input{font-size:18px!important}}

@media(max-width:760px){
  .slot-grid{grid-template-columns:repeat(6,minmax(74px,1fr))}
  .warehouse-toolbar{grid-template-columns:1fr 1fr}
}

@media(max-width:760px){
  .logo-wrap img{height:48px}
  .datetime{display:none}
  .main{padding:11px}
  .hero{min-height:165px;padding:19px}
  .hero h1{font-size:36px}
  .hero p{font-size:15px}
  .cards{grid-template-columns:1fr 1fr;gap:9px}
  .number{font-size:31px}
  .card{padding:14px}
  .gates{
    grid-template-columns:repeat(5,145px);
    overflow-x:auto;padding-bottom:5px
  }
  .two{grid-template-columns:1fr}
  .row{grid-template-columns:1fr}
  table{display:block;overflow-x:auto}
}

.slot.blocked{border-color:#b74b4b;background:#2a1016}
.slot.blocked .slot-state{color:#ff7070}
.slot.quarantine{border-color:#e0a500;background:#2b230b}
.pill{display:inline-flex;align-items:center;gap:6px;padding:5px 9px;border-radius:999px;border:1px solid #28415f;background:#091522;font-size:12px;font-weight:800}
.pill.green{border-color:#25814d;color:#57ec8e}
.pill.yellow{border-color:#9a7a00;color:#ffdc3a}
.pill.red{border-color:#903d3d;color:#ff7777}
.leit-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.leit-gate{background:#0a1727;border:1px solid #294766;border-radius:16px;padding:14px;min-height:180px}
.big-status{font-size:24px;font-weight:900;margin:8px 0}
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.metric{background:#091827;border:1px solid #203a5b;border-radius:14px;padding:12px}
.metric strong{display:block;font-size:26px;margin-top:5px}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.toolbar a{display:inline-block;text-decoration:none}
.small-btn{padding:9px 12px;border-radius:10px;background:#173352;color:white;border:1px solid #315a83}
.notice{padding:12px;border:1px solid #355675;border-radius:12px;background:#0a1727;margin:10px 0}
@media(max-width:900px){.leit-grid{grid-template-columns:repeat(2,1fr)}.metric-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:560px){.leit-grid,.metric-grid{grid-template-columns:1fr}}


.camera-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.camera-card{background:#091827;border:1px solid #294766;border-radius:16px;padding:14px}
.camera-preview{width:100%;max-height:300px;object-fit:contain;border-radius:12px;background:#050b12;margin-top:10px;display:none}
.camera-result{margin-top:10px;padding:10px;border-radius:10px;background:#0b2033;border:1px solid #315a83}
.camera-status{font-size:13px;color:#aebed0;margin-top:8px}
.camera-actions{display:flex;gap:8px;flex-wrap:wrap}
.camera-file{position:absolute;left:-9999px}
.detect-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:760px){.camera-grid,.detect-grid{grid-template-columns:1fr}}


.slot.free{border-color:#25814d;background:#0d2618}
.slot.free .slot-state{color:#57ec8e}
.slot.occupied{border-color:#9a7a00;background:#2b230b}
.slot.occupied .slot-state{color:#ffdc3a}
.slot.blocked{border-color:#903d3d;background:#2a1016}
.slot.blocked .slot-state{color:#ff7777}

</style>
"""


def get_settings(c=None):
    own = c is None
    if own: c=con()
    vals={x['setting_key']:x['setting_value'] for x in c.execute("SELECT * FROM app_settings").fetchall()}
    env_settings = {
        'notification_emails':'NOTIFICATION_EMAILS', 'smtp_host':'SMTP_HOST',
        'smtp_port':'SMTP_PORT', 'smtp_user':'SMTP_USER', 'smtp_password':'SMTP_PASSWORD',  # nosec B105
        'smtp_sender':'SMTP_SENDER', 'smtp_starttls':'SMTP_STARTTLS', 'smtp_ssl':'SMTP_SSL',
        'container_notification_emails':'CONTAINER_NOTIFICATION_EMAILS',
        'reorder_notification_emails':'REORDER_NOTIFICATION_EMAILS',
    }
    for key, env_name in env_settings.items():
        if os.environ.get(env_name) is not None:
            vals[key] = os.environ[env_name]
    if own: c.close()
    return vals

def send_system_email(event_type, subject, body, recipients=None):
    c=con(); cfg=get_settings(c)
    if recipients is None:
        key = 'container_notification_emails' if event_type == 'container_fertig' else 'reorder_notification_emails' if event_type == 'nachbestellung' else 'notification_emails'
        raw=cfg.get(key,'') or cfg.get('notification_emails','')
        recipients=[x.strip() for x in raw.replace(';',',').split(',') if x.strip()]
    if not recipients:
        c.execute("INSERT INTO email_log(event_type,recipient,subject,status,error_text,created_at) VALUES(?,?,?,?,?,?)",(event_type,'',subject,'übersprungen','Keine Empfängeradresse konfiguriert',now_iso())); c.commit(); c.close(); return False
    host=cfg.get('smtp_host','').strip(); user=cfg.get('smtp_user','').strip(); password=cfg.get('smtp_password',''); sender=cfg.get('smtp_sender','').strip() or user
    try: port=int(cfg.get('smtp_port','587') or 587)
    except: port=587
    if not host or not sender:
        err='SMTP-Server oder Absender fehlt in Einstellungen.'
        for r in recipients: c.execute("INSERT INTO email_log(event_type,recipient,subject,status,error_text,created_at) VALUES(?,?,?,?,?,?)",(event_type,r,subject,'fehler',err,now_iso()))
        c.commit(); c.close(); return False
    try:
        msg=EmailMessage(); msg['Subject']=subject; msg['From']=sender; msg['To']=', '.join(recipients); msg.set_content(body)
        if cfg.get('smtp_ssl','0')=='1':
            with smtplib.SMTP_SSL(host,port,timeout=15,context=ssl.create_default_context()) as srv:
                if user: srv.login(user,password)
                srv.send_message(msg)
        else:
            with smtplib.SMTP(host,port,timeout=15) as srv:
                srv.ehlo()
                if cfg.get('smtp_starttls','1')=='1': srv.starttls(context=ssl.create_default_context()); srv.ehlo()
                if user: srv.login(user,password)
                srv.send_message(msg)
        for r in recipients: c.execute("INSERT INTO email_log(event_type,recipient,subject,status,created_at) VALUES(?,?,?,?,?)",(event_type,r,subject,'gesendet',now_iso()))
        c.commit(); c.close(); return True
    except Exception as e:
        for r in recipients: c.execute("INSERT INTO email_log(event_type,recipient,subject,status,error_text,created_at) VALUES(?,?,?,?,?,?)",(event_type,r,subject,'fehler',str(e)[:500],now_iso()))
        c.commit(); c.close(); return False

def article_stock(c, article_no):
    row=c.execute("SELECT COALESCE(SUM(quantity),0) FROM load_carriers WHERE article_no=? AND status!='ausgelagert' AND rack IS NOT NULL",(article_no,)).fetchone()
    return int(row[0] or 0)

def check_reorders():
    c=con(); arts=c.execute("SELECT article_no,COALESCE(article_name,name,article_no) n,min_stock,target_stock FROM articles WHERE min_stock>0").fetchall(); notices=[]
    for a in arts:
        stock=article_stock(c,a['article_no']); open_alert=c.execute("SELECT * FROM reorder_alerts WHERE article_no=? AND status='offen' ORDER BY id DESC LIMIT 1",(a['article_no'],)).fetchone()
        if stock <= int(a['min_stock'] or 0):
            if not open_alert:
                cur=c.execute("INSERT INTO reorder_alerts(article_no,status,stock_at_alert,created_at) VALUES(?,'offen',?,?)",(a['article_no'],stock,now_iso())); alert_id=cur.lastrowid; c.commit()
                open_alert=c.execute("SELECT * FROM reorder_alerts WHERE id=?",(alert_id,)).fetchone()
            cutoff=(datetime.now()-timedelta(minutes=15)).isoformat(timespec='seconds')
            if open_alert and not open_alert['email_sent_at'] and (not open_alert['last_email_attempt_at'] or open_alert['last_email_attempt_at'] < cutoff):
                claimed=c.execute("""UPDATE reorder_alerts SET email_attempts=email_attempts+1,last_email_attempt_at=?
                    WHERE id=? AND email_sent_at IS NULL AND (last_email_attempt_at IS NULL OR last_email_attempt_at<?)""",
                    (now_iso(),open_alert['id'],cutoff))
                c.commit()
                if claimed.rowcount == 1:
                    target=max(int(a['target_stock'] or 0),int(a['min_stock'] or 0)); suggested=max(0,target-stock)
                    notices.append((open_alert['id'],a['article_no'],a['n'],stock,a['min_stock'],target,suggested))
        elif open_alert:
            c.execute("UPDATE reorder_alerts SET status='erledigt',closed_at=? WHERE id=?",(now_iso(),open_alert['id'])); c.commit()
    c.close()
    for alert_id,no,name,stock,min_s,target,suggested in notices:
        subject=f"Nachbestellung erforderlich: {no} – {name}"
        body=f"Artikel: {no} – {name}\nAktueller Bestand: {stock}\nMindestbestand: {min_s}\nSollbestand: {target}\nEmpfohlene Nachbestellmenge: {suggested}\nZeitpunkt: {now_iso()}\n\nLagerPro"
        ok=send_system_email('nachbestellung',subject,body)
        if ok:
            c=con(); c.execute("UPDATE reorder_alerts SET email_sent_at=? WHERE id=?",(now_iso(),alert_id)); c.commit(); c.close()

def bottom_nav(active):
    pages = [
        ("/","⌂","Dashboard","dashboard"),
        ("/articles","◈","Artikel","articles"),
        ("/containers","▣","Container","containers"),
        ("/carriers","▤","Träger","carriers"),
        ("/warehouse","▦","Lager","warehouse"),
        ("/gates","▥","Tore","gates"),
        ("/archive","◷","Archiv","archive"),
        ("/more","⋯","Mehr","more"),
    ]
    if session.get('role') == 'Admin':
        pages.append(("/users","♙","Benutzer","users"))
    html = '<div class="bottom-nav">'
    for url, icon, text, key in pages:
        cls = "active" if active == key else ""
        html += f'<a href="{url}" class="{cls}"><span class="icon">{icon}</span>{text}</a>'
    return html + "</div>"


def csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@app.before_request
def verify_csrf():
    g.csp_nonce = secrets.token_urlsafe(18)
    for key in request.values:
        for value in request.values.getlist(key):
            if len(value) > 5000 or "\x00" in value or "<" in value or ">" in value:
                abort(400, description="Eingabe enthält unzulässige Zeichen oder ist zu lang")
    token = csrf_token()
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
        if not supplied or not hmac.compare_digest(token, supplied):
            abort(400, description="Ungültige oder fehlende Sicherheitsprüfung")


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    nonce = getattr(g, "csp_nonce", "")
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; "
        f"style-src 'self' 'unsafe-inline'; script-src 'self' 'nonce-{nonce}' 'strict-dynamic' https:; "
        "worker-src 'self' blob: https://cdn.jsdelivr.net; connect-src 'self' https://cdn.jsdelivr.net; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers.setdefault("Cache-Control", "no-store")
    return response

def page(content, active="dashboard"):
    now = datetime.now()
    logged_in = bool(session.get("user_id"))
    # Ohne Anmeldung keine Navigation und keine Lagerdaten in der Oberfläche.
    profile = (f'<div class="profile"><div class="avatar">{(session.get("username") or "LP")[:2].upper()}</div>'
               f'<div class="datetime">{now.strftime("%d.%m.%Y")}<br>{now.strftime("%H:%M")} Uhr</div></div>') if logged_in else ""
    nav = bottom_nav(active) if logged_in else ""
    body_class = "" if logged_in else "auth-only"
    token = csrf_token()
    content = re.sub(
        r"(<form\b[^>]*method=[\"']post[\"'][^>]*>)",
        lambda match: match.group(1) + f'<input type="hidden" name="csrf_token" value="{token}">',
        content,
        flags=re.I,
    )
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#07111f">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="LagerPro">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="apple-touch-icon" href="/app-icon.svg">
<title>LagerPro</title>
{STYLE}
</head>
<body class="{body_class}">
<header class="topbar">
  <div class="top-inner">
    <div class="logo-wrap">
      <img src="{LOGO_DATA}" alt="drive MEDICAL">
    </div>
    {profile}
  </div>
</header>
<main class="main">{content}</main>
{nav}
<script nonce="{g.csp_nonce}">
if ("serviceWorker" in navigator) {{ navigator.serviceWorker.register("/sw.js").catch(()=>{{}}); }}
</script>
</body>
</html>"""

@app.route("/")
def dashboard():
    c = con()
    containers = c.execute(
        "SELECT * FROM containers WHERE status!='erledigt' ORDER BY id DESC"
    ).fetchall()
    total_places = c.execute("SELECT COUNT(*) FROM warehouse_slots").fetchone()[0]
    occupied = c.execute(
        "SELECT COUNT(*) FROM warehouse_slots WHERE load_carrier_id IS NOT NULL"
    ).fetchone()[0]
    blocked = c.execute("SELECT COUNT(*) FROM warehouse_slots WHERE slot_status='gesperrt'").fetchone()[0]
    open_tasks = c.execute("SELECT COUNT(*) FROM tasks WHERE status='offen'").fetchone()[0]
    quarantine = c.execute("SELECT COUNT(*) FROM load_carriers WHERE quality_status='quarantaene'").fetchone()[0]
    sync_waiting = c.execute("SELECT COUNT(*) FROM sage_sync_queue WHERE status IN ('wartet','fehler')").fetchone()[0]
    c.close()

    free = max(0, total_places - occupied - blocked)
    percent = round(occupied / total_places * 100) if total_places else 0

    gates = {g: None for g in range(8, 13)}
    for item in containers:
        if item["gate_no"] in gates and gates[item["gate_no"]] is None:
            gates[item["gate_no"]] = item

    html = f"""
    <section class="hero">
      <div class="hero-content">
        <div class="hero-small">WILLKOMMEN BEI</div>
        <h1>Lagerprozess</h1>
        <p>Übersicht · Kontrolle · Effiziente Lagerhaltung</p>
      </div>
    </section>

    <section class="action-grid">
      <a class="action-card" href="/control"><b>▦ Wareneingangs-Leitstand</b><span class="muted">Tore 8–12 · Fortschritt · Probleme</span></a>
      <a class="action-card" href="/store"><b>⌁ Scan-Einlagerung</b><span class="muted">Ladungsträger + Lagerplatz</span></a>
      <a class="action-card" href="/search"><b>⌕ Wo ist meine Ware?</b><span class="muted">Artikel · Seriennummer · Ladungsträger</span></a>
      <a class="action-card" href="/camera"><b>◉ Kamera-Scan</b><span class="muted">Träger, Artikel und Lagerplatz fotografieren</span></a>
      <a class="action-card" href="/manual-booking"><b>✎ Manuell buchen</b><span class="muted">Artikelnummer direkt auf Lagerplatz buchen</span></a>
    </section>

    <section class="cards">
      <div class="card">
        <div class="card-title">Gesamtstellplätze</div>
        <div class="number">{total_places}</div>
        <div class="muted">30 Regale × 4 Ebenen × 83 Positionen · Position 21–23 = 3er, sonst 4er</div>
      </div>

      <div class="card">
        <div class="card-title">Belegte Stellplätze</div>
        <div class="number">{occupied}</div>
        <div class="muted">{percent} % Auslastung</div>
        <div class="progress"><span style="width:{percent}%"></span></div>
      </div>

      <div class="card">
        <div class="card-title">Freie Stellplätze</div>
        <div class="number">{free}</div>
        <div class="muted">{100-percent} % verfügbar</div>
      </div>

      <div class="card">
        <div class="card-title">Aktive Container</div>
        <div class="number">{len(containers)}</div>
        <div class="muted">Tore 8–12</div>
      </div>
    </section>

    <section class="card">
      <div class="section-head"><h2>Betriebsstatus</h2><a class="yellow-link" href="/reports">Auswertungen →</a></div>
      <div class="metric-grid">
        <div class="metric"><span class="muted">Gesperrte Plätze</span><strong>{blocked}</strong></div>
        <div class="metric"><span class="muted">Offene Aufträge</span><strong>{open_tasks}</strong></div>
        <div class="metric"><span class="muted">Quarantäne</span><strong>{quarantine}</strong></div>
        <div class="metric"><span class="muted">Sage-Sync offen</span><strong>{sync_waiting}</strong></div>
      </div>
      <div class="toolbar">
        <a class="small-btn" href="/tasks">Arbeitsaufträge</a>
        <a class="small-btn" href="/inventory">Inventur</a>
        <a class="small-btn" href="/quality">Qualität</a>
        <a class="small-btn" href="/slot-admin">Sperrplätze</a>
        <a class="small-btn" href="/sync">Sage-Sync</a>
      </div>
    </section>

    <section class="card">
      <div class="section-head">
        <h2>Tore 8–12</h2>
        <a href="/gates" class="yellow-link">Alle anzeigen →</a>
      </div>
      <div class="gates">
    """

    for gate in range(8, 13):
        item = gates[gate]
        if not item:
            html += f"""
            <div class="gate">
              <div class="gate-number">Tor {gate}</div>
              <span class="dot gray"></span><br>
              <span class="muted">Frei</span>
            </div>
            """
        else:
            status = (item["status"] or "").lower()
            if "versp" in status:
                dot, status_class = "red", "status-red"
            elif "bereit" in status or "vor ort" in status:
                dot, status_class = "green", "status-green"
            else:
                dot, status_class = "yellow-dot", "status-yellow"

            html += f"""
            <div class="gate">
              <div class="gate-number">Tor {gate}</div>
              <span class="dot {dot}"></span><br>
              <b>{item["container_no"]}</b><br>
              <span class="{status_class}">{item["status"]}</span>
            </div>
            """

    html += f"""
      </div>
    </section>

    <section class="two">
      <div class="card">
        <div class="section-head"><h2>Lagerauslastung</h2></div>
        <div class="donut-wrap">
          <div class="donut" style="background:conic-gradient(var(--green) 0 {percent}%,#7896bd {percent}% 100%)">
            <div class="donut-inner">
              <div>
                <div class="donut-number">{percent}%</div>
                <div class="muted">Auslastung</div>
              </div>
            </div>
          </div>
          <div>
            <p>🟢 Belegt <b>{occupied}</b></p>
            <p>🔵 Frei <b>{free}</b></p>
            <p class="muted">Von {total_places} Stellplätzen</p>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="section-head">
          <h2>Aktuelle Container</h2>
          <a href="/containers" class="yellow-link">Alle anzeigen →</a>
        </div>
        <table>
          <tr><th>Container</th><th>Status</th><th>Tor</th></tr>
    """

    if containers:
        for item in containers[:6]:
            html += f"""
            <tr>
              <td><a style="color:white" href="/container/{item["id"]}">{item["container_no"]}</a></td>
              <td>{item["status"]}</td>
              <td>{item["gate_no"] or "–"}</td>
            </tr>
            """
    else:
        html += '<tr><td colspan="3" class="muted">Noch keine Container.</td></tr>'

    html += "</table></div></section>"
    return page(html, "dashboard")


@app.route("/articles", methods=["GET", "POST"])
def articles():
    c = con()
    if request.method == "POST":
        units = max(1, int(request.form.get("units_per_carton", 1)))
        cartons_per_pallet = max(1, int(request.form.get("cartons_per_pallet", 1)))
        pallet_type = request.form.get("ptype", "Euro")
        storage_rule = request.form.get("rule", "Alle Ebenen")
        if pallet_type not in {"Euro","Einweg","Einweg 115 x 115"} or storage_rule not in {"Alle Ebenen","Nur Ebene 1","Nur Ebene 2-4"}:
            abort(400, description="Ungültige Artikelstammdaten")
        c.execute("""
        INSERT INTO articles(article_no,name,article_name,pallet_type,cpp,storage_rule,units_per_carton)
        VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(article_no) DO UPDATE SET
          name=excluded.name,
          article_name=excluded.article_name,
          pallet_type=excluded.pallet_type,
          cpp=excluded.cpp,
          storage_rule=excluded.storage_rule,
          units_per_carton=excluded.units_per_carton
        """, (
            request.form["no"].strip(),
            request.form["name"].strip(),
            request.form["name"].strip(),
            pallet_type,
            cartons_per_pallet,
            storage_rule,
            units
        ))
        c.commit(); c.close()
        return redirect("/articles")

    rows = c.execute("SELECT * FROM articles ORDER BY article_no").fetchall()
    c.close()
    html = """
    <div class="kicker">ARTIKELSTAMM</div>
    <h1 class="page-title">Artikel verwalten</h1>
    <div class="card">
      <form method="post">
        <div class="row">
          <div>Artikelnummer<input name="no" required></div>
          <div>Artikelname<input name="name" required></div>
        </div>
        <div class="row">
          <div>Artikel pro Karton<input type="number" min="1" name="units_per_carton" required></div>
          <div>Kartons pro Palette<input type="number" min="1" name="cartons_per_pallet" required></div>
          <div>Palettentyp<select name="ptype">
            <option>Euro</option><option>Einweg</option><option>Einweg 115 x 115</option>
          </select></div>
        </div>
        Lageregel
        <select name="rule">
          <option>Alle Ebenen</option><option>Nur Ebene 1</option><option>Nur Ebene 2-4</option>
        </select>
        <button>Artikel speichern</button>
      </form>
    </div>
    <div class="card"><table>
      <tr><th>Nr.</th><th>Name</th><th>Artikel/Karton</th><th>Kartons/Palette</th><th>Palette</th><th>Regel</th></tr>
    """
    for x in rows:
        html += f"""<tr><td>{x["article_no"]}</td><td>{x["name"]}</td>
        <td><b>{x["units_per_carton"]}</b></td><td>{x["cpp"]}</td><td>{x["pallet_type"]}</td><td>{x["storage_rule"]}</td></tr>"""
    html += "</table></div>"
    return page(html, "articles")


@app.route("/containers", methods=["GET", "POST"])
def containers():
    c = con()
    if request.method == "POST":
        gate = int(request.form["gate"]) if request.form.get("gate") else None
        status = request.form.get("status", "geplant")
        if gate is not None and gate not in range(8,13): abort(400)
        if status not in {"geplant","vor Ort","verspätet","Entladung","bereit","erledigt"}: abort(400)
        c.execute("""INSERT INTO containers(container_no,gate_no,status,created_at)
                     VALUES(?,?,?,?)""",
                  (request.form["no"].strip(), gate, status,
                   datetime.now().isoformat(timespec="minutes")))
        c.commit(); c.close()
        return redirect("/containers")

    rows = c.execute("SELECT * FROM containers ORDER BY id DESC").fetchall()
    c.close()
    gates = "".join(f"<option>{x}</option>" for x in range(8,13))
    html = f"""
    <div class="kicker">WARENEINGANG</div><h1 class="page-title">Container</h1>
    <div class="card"><form method="post">
      Containernummer<input name="no" required>
      <div class="row"><div>Tor<select name="gate"><option value="">Kein Tor</option>{gates}</select></div>
      <div>Status<select name="status">
        <option>geplant</option><option>vor Ort</option><option>verspätet</option>
        <option>Entladung</option><option>bereit</option><option>erledigt</option>
      </select></div></div>
      <button>Container anlegen</button>
    </form></div>
    <div class="card"><table><tr><th>Container</th><th>Tor</th><th>Status</th></tr>
    """
    for x in rows:
        html += f"""<tr><td><a style="color:white" href="/container/{x["id"]}">{x["container_no"]}</a></td>
        <td>{x["gate_no"] or "–"}</td><td><span class="badge">{x["status"]}</span></td></tr>"""
    html += "</table></div>"
    return page(html, "containers")


@app.route("/container/<int:cid>", methods=["GET", "POST"])
def container_detail(cid):
    c = con()
    cont = c.execute("SELECT * FROM containers WHERE id=?", (cid,)).fetchone()
    if not cont:
        c.close(); return redirect("/containers")

    if request.method == "POST":
        art = c.execute("SELECT * FROM articles WHERE article_no=?",
                        (request.form["article"],)).fetchone()
        if art:
            cartons = max(1, int(request.form["cartons"]))
            upc = max(1, int(art["units_per_carton"]))
            count = cartons * upc
            c.execute("""INSERT INTO items
                (container_id,article_no,name,cartons,cpp,pallet_type,units_per_carton,article_count)
                VALUES(?,?,?,?,?,?,?,?)""",
                (cid,art["article_no"],art["name"],cartons,1,art["pallet_type"],upc,count))
            c.commit()
        c.close(); return redirect(f"/container/{cid}")

    arts = c.execute("SELECT * FROM articles ORDER BY article_no").fetchall()
    items = c.execute("SELECT * FROM items WHERE container_id=? ORDER BY id DESC",(cid,)).fetchall()
    carriers = c.execute("SELECT * FROM load_carriers WHERE container_id=? ORDER BY id DESC",(cid,)).fetchall()
    c.close()

    html = f"""
    <div class="kicker">CONTAINERDETAIL</div><h1 class="page-title">{cont["container_no"]}</h1>
    <div class="card"><b>Tor {cont["gate_no"] or "–"}</b> &nbsp; <span class="badge">{cont["status"]}</span></div>
    <div class="card"><form method="post" action="/container/{cid}/finish" onsubmit="return confirm('Container wirklich als fertig markieren?')"><button>✓ Container fertig buchen & E-Mail senden</button></form><p class="muted">Beim Abschluss wird der konfigurierte Vorgesetzte automatisch per E-Mail informiert.</p></div>
    <div class="card"><h2>Ware erfassen</h2>
    <p class="muted">Kartonanzahl wird nur im Wareneingang erfasst. Der Bestand wird als Artikelanzahl geführt.</p>
    """
    if arts:
        html += '<form method="post">Artikel<select name="article">'
        for a in arts:
            html += f'<option value="{a["article_no"]}">{a["article_no"]} – {a["name"]} · {a["units_per_carton"]} Artikel/Karton</option>'
        html += '</select>Kartonanzahl<input type="number" min="1" name="cartons" required><button>Ware übernehmen</button></form>'
    else:
        html += '<p class="muted">Bitte zuerst einen Artikel anlegen.</p>'
    html += """</div><div class="card"><h2>Containerinhalt</h2>
      <table><tr><th>Artikel</th><th>Kartons</th><th>Artikel/Karton</th><th>Artikelanzahl</th></tr>"""
    total_units = 0
    for x in items:
        total_units += x["article_count"]
        html += f"""<tr><td>{x["article_no"]}<br><span class="muted">{x["name"]}</span></td>
        <td>{x["cartons"]}</td><td>{x["units_per_carton"]}</td><td><b>{x["article_count"]}</b></td></tr>"""
    html += f"</table><h3>Gesamte Artikelanzahl: {total_units}</h3></div>"
    html += f"""<div class="card"><div class="section-head"><h2>Ladungsträger</h2>
      <a class="yellow-link" href="/carriers/new?container_id={cid}">+ Ladungsträger scannen →</a></div>"""
    if carriers:
        html += "<table><tr><th>Träger</th><th>Artikel</th><th>Menge</th><th>Status</th></tr>"
        for lt in carriers:
            html += f"""<tr><td><a style="color:white" href="/carrier/{lt["id"]}">{lt["carrier_no"]}</a></td>
            <td>{lt["article_no"] or "–"}</td><td>{lt["quantity"]}</td><td>{lt["status"]}</td></tr>"""
        html += "</table>"
    else:
        html += '<p class="muted">Noch kein Ladungsträger für diesen Container.</p>'
    html += "</div>"
    return page(html, "containers")


@app.route("/carriers")
def carriers():
    c=con()
    rows=c.execute("""SELECT lc.*, c.container_no FROM load_carriers lc
                      LEFT JOIN containers c ON c.id=lc.container_id ORDER BY lc.id DESC""").fetchall()
    c.close()
    html="""<div class="kicker">LADUNGSTRÄGER</div><h1 class="page-title">Ladungsträger</h1>
    <div class="action-grid">
      <a class="action-card" href="/carriers/new"><b>＋ Träger erfassen</b><span class="muted">Nummer scannen und Ware aufnehmen</span></a>
      <a class="action-card" href="/store"><b>⌁ Einlagern</b><span class="muted">Träger + Lagerplatz scannen</span></a>
      <a class="action-card" href="/search"><b>⌕ Suchen</b><span class="muted">Träger, Artikel oder Seriennummer finden</span></a>
    </div><div class="card"><table><tr><th>Träger</th><th>Artikel</th><th>Menge</th><th>Platz</th><th>Status</th></tr>"""
    for x in rows:
        slot = f'{x["rack"]}/{x["level"]}/{x["position"]}' if x["rack"] else "–"
        html += f"""<tr><td><a style="color:white" href="/carrier/{x["id"]}">{x["carrier_no"]}</a></td>
        <td>{x["article_no"] or "–"}</td><td>{x["quantity"]}</td><td>{slot}</td><td>{x["status"]}</td></tr>"""
    html += "</table></div>"
    return page(html,"carriers")


@app.route("/carriers/new", methods=["GET","POST"])
def carrier_new():
    c=con()
    if request.method=="POST":
        no=request.form["carrier_no"].strip()
        cid=int(request.form["container_id"]) if request.form.get("container_id") else None
        if no:
            try:
                c.execute("""INSERT INTO load_carriers(carrier_no,container_id,status,created_at)
                             VALUES(?,?,?,?)""",(no,cid,"offen",datetime.now().isoformat(timespec="minutes")))
                c.commit()
                new_id=c.execute("SELECT id FROM load_carriers WHERE carrier_no=?",(no,)).fetchone()["id"]
                c.execute("""INSERT INTO movements(load_carrier_id,carrier_no,movement_type,created_at)
                             VALUES(?,?,?,?)""",(new_id,no,"Ladungsträger erstellt",datetime.now().isoformat(timespec="minutes")))
                c.commit(); c.close()
                return redirect(f"/carrier/{new_id}")
            except INTEGRITY_ERRORS:
                c.rollback()
                existing=c.execute("SELECT id FROM load_carriers WHERE carrier_no=?",(no,)).fetchone()
                c.close()
                return redirect(f'/carrier/{existing["id"]}')
    containers=c.execute("SELECT * FROM containers WHERE status!='erledigt' ORDER BY id DESC").fetchall()
    c.close()
    selected=request.args.get("container_id","")
    opts='<option value="">Ohne Container</option>'
    for x in containers:
        sel="selected" if str(x["id"])==selected else ""
        opts += f'<option value="{x["id"]}" {sel}>{x["container_no"]}</option>'
    html=f"""<div class="kicker">SCAN 1/3</div><h1 class="page-title">Ladungsträger erfassen</h1>
    <div class="scanbox"><form method="post">
      Ladungsträgernummer scannen
      <input class="scan-input" name="carrier_no" autofocus autocomplete="off" required placeholder="LT scannen …">
      Herkunftscontainer<select name="container_id">{opts}</select>
      <button>Ladungsträger öffnen</button>
    </form></div></div>"""
    return page(html,"carriers")


@app.route("/carrier/<int:lid>", methods=["GET","POST"])
def carrier_detail(lid):
    c=con()
    lt=c.execute("SELECT * FROM load_carriers WHERE id=?",(lid,)).fetchone()
    if not lt:
        c.close(); return redirect("/carriers")
    message=""
    if request.method=="POST":
        action=request.form.get("action")
        if action=="article":
            art=c.execute("SELECT * FROM articles WHERE article_no=?",(request.form["article_no"],)).fetchone()
            if art:
                qty=max(1,int(request.form.get("quantity",1)))
                c.execute("""UPDATE load_carriers SET article_no=?,article_name=?,quantity=?,pallet_type=?
                             WHERE id=?""",(art["article_no"],art["name"],qty,art["pallet_type"],lid))
                c.commit()
        elif action=="serial":
            serial=request.form.get("serial_no","").strip()
            if serial:
                try:
                    c.execute("""INSERT INTO serial_numbers(load_carrier_id,serial_no,created_at)
                                 VALUES(?,?,?)""",(lid,serial,datetime.now().isoformat(timespec="minutes")))
                    c.commit()
                except INTEGRITY_ERRORS:
                    c.rollback()
                    message="Seriennummer ist bereits im System."
        elif action=="close":
            c.execute("UPDATE load_carriers SET status='bereit',closed_at=? WHERE id=?",
                      (datetime.now().isoformat(timespec="minutes"),lid)); c.commit()
        c.close(); return redirect(f"/carrier/{lid}")

    arts=c.execute("SELECT * FROM articles ORDER BY article_no").fetchall()
    serials=c.execute("SELECT * FROM serial_numbers WHERE load_carrier_id=? ORDER BY id DESC",(lid,)).fetchall()
    c.close()
    slot=f'{lt["rack"]}/{lt["level"]}/{lt["position"]}' if lt["rack"] else "noch nicht eingelagert"
    html=f"""<div class="kicker">LADUNGSTRÄGER</div><h1 class="page-title">{lt["carrier_no"]}</h1>
    <div class="card"><div class="row"><div><span class="muted">Status</span><h2>{lt["status"]}</h2></div>
    <div><span class="muted">Lagerplatz</span><h2>{slot}</h2></div></div></div>"""
    if not lt["article_no"]:
        html += '<div class="card"><h2>Ware auf Träger buchen</h2><form method="post"><input type="hidden" name="action" value="article">Artikel<select name="article_no">'
        for a in arts:
            html += f'<option value="{a["article_no"]}">{a["article_no"]} – {a["name"]}</option>'
        html += '</select>Artikelanzahl<input type="number" name="quantity" min="1" required><button>Ware übernehmen</button></form></div>'
    else:
        html += f"""<div class="card"><h2>{lt["article_no"]} – {lt["article_name"]}</h2>
        <div class="number">{lt["quantity"]}</div><div class="muted">Artikel auf diesem Ladungsträger</div></div>
        <div class="scanbox"><h2>Seriennummer scannen</h2>
        <form method="post"><input type="hidden" name="action" value="serial">
        <input class="scan-input" name="serial_no" autofocus autocomplete="off" required placeholder="Seriennummer …">
        <button>Seriennummer übernehmen</button></form>
        <p class="muted">Erfasst: <b>{len(serials)}</b> Seriennummern</p></div>"""
        if serials:
            html += '<div class="card"><table><tr><th>Seriennummer</th><th>Zeit</th></tr>'
            for s in serials[:100]:
                html += f'<tr><td>{s["serial_no"]}</td><td>{s["created_at"]}</td></tr>'
            html += '</table></div>'
        if lt["status"]=="offen":
            html += '<div class="card"><form method="post"><input type="hidden" name="action" value="close"><button>Ladungsträger abschließen</button></form></div>'
        elif not lt["rack"]:
            html += f'<div class="card"><a class="yellow-link" href="/store?carrier={lt["carrier_no"]}">Weiter zur Einlagerung →</a></div>'
        if lt["rack"] and lt["status"]=="eingelagert":
            html += f'<div class="card"><h2>Warenausgang</h2><form method="post" action="/carrier/{lid}/outbound" onsubmit="return confirm(\'Ladungsträger wirklich auslagern?\')"><button>↑ Ladungsträger auslagern</button></form></div>'
    html += f"""
    <div class="card">
      <h2>Qualitätsstatus</h2>
      <form method="post" action="/carrier/{lid}/quality">
        <select name="quality_status">
          <option value="frei" {"selected" if lt["quality_status"]=="frei" else ""}>Frei</option>
          <option value="quarantaene" {"selected" if lt["quality_status"]=="quarantaene" else ""}>Quarantäne</option>
          <option value="gesperrt" {"selected" if lt["quality_status"]=="gesperrt" else ""}>Gesperrt</option>
        </select>
        <input name="quality_note" value="{lt["quality_note"] or ""}" placeholder="Grund / Hinweis">
        <button>Qualitätsstatus speichern</button>
      </form>
    </div>
    """
    return page(html,"carriers")


def parse_slot(code):
    """Lagerplatz robust lesen. Akzeptiert z. B. 3/2/40 und 3-2-40.

    Gang 1-7 haben 89 Positionen, alle weiteren Gänge 83.
    """
    try:
        normalized=(code or "").strip().replace("-", "/")
        parts=[x.strip() for x in normalized.split("/") if x.strip()]
        if len(parts) != 3:
            return None
        r,l,p=[int(x) for x in parts]
        max_position=89 if 1 <= r <= 7 else 83
        if 1<=r<=30 and 1<=l<=4 and 1<=p<=max_position:
            return r,l,p
    except (TypeError, ValueError):
        pass
    return None


@app.route("/store", methods=["GET","POST"])
def store():
    msg=""
    carrier_pref=request.args.get("carrier","")
    if request.method=="POST":
        carrier_no=request.form.get("carrier_no","").strip()
        slot_code=request.form.get("slot_code","").strip()
        parsed=parse_slot(slot_code)
        c=con()
        lt=c.execute("SELECT * FROM load_carriers WHERE carrier_no=?",(carrier_no,)).fetchone()
        if not lt:
            msg="Ladungsträger nicht gefunden."
        elif lt["status"] not in ("bereit","eingelagert"):
            msg="Ladungsträger zuerst abschließen."
        elif not parsed:
            msg="Lagerplatz ungültig. Format z. B. 22/1/82."
        else:
            r,l,p=parsed
            slot=c.execute("SELECT * FROM warehouse_slots WHERE rack=? AND level=? AND position=?",(r,l,p)).fetchone()
            art=c.execute("SELECT * FROM articles WHERE article_no=?",(lt["article_no"],)).fetchone()
            rule=art["storage_rule"] if art else "Alle Ebenen"
            if slot["slot_status"]=="gesperrt":
                msg=f'Dieser Lagerplatz ist gesperrt: {slot["block_reason"] or "kein Grund angegeben"}.'
            elif slot["load_carrier_id"] and slot["load_carrier_id"] != lt["id"]:
                msg="Dieser Lagerplatz ist bereits belegt."
            elif lt["quality_status"] in ("quarantaene","gesperrt"):
                msg="Dieser Ladungsträger ist qualitativ gesperrt und darf nicht normal eingelagert werden."
            elif rule=="Nur Ebene 1" and l!=1:
                msg="Dieser Artikel darf nur auf Ebene 1."
            elif rule=="Nur Ebene 2-4" and l==1:
                msg="Dieser Artikel darf nur auf Ebene 2–4."
            else:
                # Prevent Euro and Einweg directly next to each other.
                neighbors=c.execute("""SELECT pallet_type FROM warehouse_slots
                    WHERE rack=? AND level=? AND position IN (?,?) AND load_carrier_id IS NOT NULL""",
                    (r,l,p-1,p+1)).fetchall()
                this_euro=(lt["pallet_type"]=="Euro")
                conflict=any((n["pallet_type"]=="Euro") != this_euro for n in neighbors if n["pallet_type"])
                if conflict:
                    msg="Nicht möglich: Euro und Einweg dürfen nicht direkt nebeneinander stehen."
                else:
                    old=f'{lt["rack"]}/{lt["level"]}/{lt["position"]}' if lt["rack"] else None
                    if lt["rack"]:
                        c.execute("""UPDATE warehouse_slots SET article_no=NULL,article_name=NULL,pallet_type=NULL,
                                     quantity=NULL,container_id=NULL,occupied_at=NULL,load_carrier_no=NULL,load_carrier_id=NULL,
                                     slot_status='frei'
                                     WHERE load_carrier_id=?""",(lt["id"],))
                    now=datetime.now().isoformat(timespec="minutes")
                    updated=c.execute("""UPDATE warehouse_slots SET article_no=?,article_name=?,pallet_type=?,quantity=?,
                                 container_id=?,occupied_at=?,load_carrier_no=?,load_carrier_id=?,slot_status='belegt'
                                 WHERE rack=? AND level=? AND position=? AND load_carrier_id IS NULL AND slot_status='frei'""",
                              (lt["article_no"],lt["article_name"],lt["pallet_type"],lt["quantity"],
                               lt["container_id"],now,lt["carrier_no"],lt["id"],r,l,p))
                    if updated.rowcount != 1:
                        c.rollback(); c.close()
                        return page('<div class="notice danger">Der Zielplatz wurde gleichzeitig belegt. Die Umlagerung wurde vollständig zurückgenommen.</div>',"warehouse"),409
                    c.execute("""UPDATE load_carriers SET rack=?,level=?,position=?,status='eingelagert',stored_at=?
                                 WHERE id=?""",(r,l,p,now,lt["id"]))
                    c.execute("""INSERT INTO movements(load_carrier_id,carrier_no,movement_type,article_no,quantity,from_slot,to_slot,created_at)
                                 VALUES(?,?,?,?,?,?,?,?)""",(lt["id"],lt["carrier_no"],"Einlagerung/Umlagerung",lt["article_no"],lt["quantity"],old,slot_code,now))
                    c.commit()
                    c.close()
                    return redirect(f"/carrier/{lt['id']}")
        c.close()
    html=f"""<div class="kicker">SCAN 3/3</div><h1 class="page-title">Einlagern</h1>
    <div class="scanbox"><form method="post">
      Ladungsträger scannen<input class="scan-input" name="carrier_no" value="{carrier_pref}" required autocomplete="off" placeholder="Ladungsträger …">
      Lagerplatz scannen<input class="scan-input" name="slot_code" required autocomplete="off" placeholder="z. B. 22/1/82">
      <button>Einlagerung bestätigen</button>
    </form></div>"""
    if msg: html += f'<div class="card"><b class="danger">{msg}</b></div>'
    html += '<div class="card"><p class="muted">Die App prüft Belegung, Ebenenregel und Euro/Einweg-Nachbarschaft vor der Buchung.</p></div>'
    return page(html,"warehouse")


@app.route('/carrier/<int:lid>/outbound',methods=['POST'])
def outbound_carrier(lid):
    c=con(); lt=c.execute("SELECT * FROM load_carriers WHERE id=?",(lid,)).fetchone()
    if not lt: c.close(); return redirect('/stock')
    old=f"{lt['rack']}/{lt['level']}/{lt['position']}" if lt['rack'] else None; now=now_iso()
    c.execute("UPDATE warehouse_slots SET article_no=NULL,article_name=NULL,pallet_type=NULL,quantity=NULL,container_id=NULL,occupied_at=NULL,load_carrier_no=NULL,load_carrier_id=NULL,slot_status='frei' WHERE load_carrier_id=?",(lid,))
    c.execute("UPDATE load_carriers SET status='ausgelagert',rack=NULL,level=NULL,position=NULL WHERE id=?",(lid,))
    c.execute("INSERT INTO movements(load_carrier_id,carrier_no,movement_type,article_no,quantity,from_slot,created_at) VALUES(?,?,?,?,?,?,?)",(lid,lt['carrier_no'],'Auslagerung',lt['article_no'],lt['quantity'],old,now)); c.commit(); c.close(); check_reorders(); audit('Auslagerung','carrier',lid); return redirect('/stock')

@app.route("/warehouse")
def warehouse():
    try:r=max(1,min(30,int(request.args.get("rack",1))))
    except:r=1
    try:l=max(1,min(4,int(request.args.get("level",1))))
    except:l=1
    c=con()
    maxpos=89 if r<=7 else 83
    slots=c.execute("SELECT * FROM warehouse_slots WHERE rack=? AND level=? AND position<=? ORDER BY position",(r,l,maxpos)).fetchall()
    occ=c.execute("SELECT COUNT(*) FROM warehouse_slots WHERE rack=? AND level=? AND position<=? AND load_carrier_id IS NOT NULL",(r,l,maxpos)).fetchone()[0]
    blocked=c.execute("SELECT COUNT(*) FROM warehouse_slots WHERE rack=? AND level=? AND position<=? AND slot_status='gesperrt'",(r,l,maxpos)).fetchone()[0]
    reserved=c.execute("SELECT COUNT(*) FROM warehouse_slots WHERE rack=? AND level=? AND position<=? AND slot_status='reserviert'",(r,l,maxpos)).fetchone()[0]
    free=max(0,maxpos-occ-blocked-reserved)
    c.close()
    ropts="".join(f'<option value="{x}" {"selected" if x==r else ""}>Gang {x}</option>' for x in range(1,31))
    lopts="".join(f'<option value="{x}" {"selected" if x==l else ""}>Ebene {x}</option>' for x in range(1,5))
    html=f"""<div class="kicker">LAGER</div><div class="toolbar"><span class="pill green">GRÜN = FREI</span><span class="pill yellow">GELB = BELEGT</span><span class="pill red">ROT = GESPERRT</span></div><h1 class="page-title">Lagerübersicht</h1><div class="notice"><b>Lagerstruktur:</b> Gang 1–7 haben jeweils 89 Positionen. Ab Gang 8 gelten 83 Positionen. Positionen 21, 22 und 23 sind in jedem Gang 3er-Stellplätze; alle übrigen Positionen sind 4er-Stellplätze.</div>
    <div class="card"><div class="section-head"><h2>Ansicht wählen</h2><a class="button" href="/batch-booking?gang={r}&level={l}">☑ Mehrfachauswahl</a></div><form method="get" class="warehouse-toolbar">
      <div>Gang<select name="rack" onchange="this.form.submit()">{ropts}</select></div>
      <div>Ebene<select name="level" onchange="this.form.submit()">{lopts}</select></div>
    </form><div class="row"><div><span class="muted">Belegt</span><div class="number">{occ}</div></div>
    <div><span class="muted">Frei</span><div class="number">{free}</div></div></div></div>
    <div class="card"><div class="section-head"><h2>Gang {r} · Ebene {l}</h2><span class="muted">{maxpos} Positionen · 21–23 sind 3er</span></div><div class="slot-grid">"""
    for s in slots:
        code=f'{r}/{l}/{s["position"]}'
        if s["slot_status"]=="gesperrt":
            html += f"""<div class="slot blocked"><div class="slot-code">{code}</div>
              <div class="slot-info">{s["block_reason"] or "Gesperrt"}<br><span class="muted">{s["capacity"]}er-Stellplatz</span></div><div class="slot-state">GESPERRT</div></div>"""
        elif s["load_carrier_id"]:
            html += f"""<a class="slot occupied" href="/carrier/{s["load_carrier_id"]}">
              <div class="slot-code">{code}</div><div class="slot-info">{s["load_carrier_no"]}<br>{s["article_no"]}<br><span class="muted">{s["capacity"]}er-Stellplatz</span></div>
              <div class="slot-state">BELEGT</div></a>"""
        else:
            html += f"""<a class="slot free" href="/manual-booking?slot_code={code}">
              <div class="slot-code">{code}</div>
              <div class="slot-info">Freier Lagerplatz<br><span class="muted">{s["capacity"]}er-Stellplatz · Zum Einlagern anklicken</span></div>
              <div class="slot-state">FREI</div></a>"""
    html += "</div></div>"
    return page(html,"warehouse")


@app.route("/search", methods=["GET"])
def search_page():
    q=request.args.get("q","").strip()
    results=[]
    if q:
        c=con()
        results=c.execute("""SELECT DISTINCT lc.* FROM load_carriers lc
          LEFT JOIN serial_numbers sn ON sn.load_carrier_id=lc.id
          WHERE lc.carrier_no LIKE ? OR lc.article_no LIKE ? OR lc.article_name LIKE ? OR sn.serial_no LIKE ?
          ORDER BY lc.id DESC LIMIT 100""",(f"%{q}%",f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
        c.close()
    html=f"""<div class="kicker">SUCHE</div><h1 class="page-title">Ware finden</h1>
    <div class="scanbox"><form method="get"><input class="scan-input" name="q" value="{q}" autofocus
    placeholder="Artikel, Seriennummer oder Ladungsträger …"><button>Suchen</button></form></div>"""
    if q:
        html += '<div class="card"><table><tr><th>Träger</th><th>Artikel</th><th>Platz</th><th>Status</th></tr>'
        for x in results:
            slot=f'{x["rack"]}/{x["level"]}/{x["position"]}' if x["rack"] else "–"
            html += f'<tr><td><a style="color:white" href="/carrier/{x["id"]}">{x["carrier_no"]}</a></td><td>{x["article_no"] or "–"}</td><td><b>{slot}</b></td><td>{x["status"]}</td></tr>'
        if not results: html += '<tr><td colspan="4" class="muted">Nichts gefunden.</td></tr>'
        html += "</table></div>"
    return page(html,"carriers")


@app.route("/archive")
def archive():
    c=con()
    moves=c.execute("SELECT * FROM movements ORDER BY id DESC LIMIT 250").fetchall()
    c.close()
    html="""<div class="kicker">ARCHIV</div><h1 class="page-title">Bewegungsverlauf</h1>
    <div class="card"><table><tr><th>Zeit</th><th>Ladungsträger</th><th>Vorgang</th><th>Von</th><th>Nach</th></tr>"""
    for m in moves:
        html += f'<tr><td>{m["created_at"]}</td><td>{m["carrier_no"] or "–"}</td><td>{m["movement_type"]}</td><td>{m["from_slot"] or "–"}</td><td>{m["to_slot"] or "–"}</td></tr>'
    html += "</table></div>"
    return page(html,"archive")



@app.route("/control")
def control_center():
    c=con()
    active=c.execute("SELECT * FROM containers WHERE status!='erledigt' ORDER BY gate_no,id DESC").fetchall()
    gates={g:None for g in range(8,13)}
    for x in active:
        if x["gate_no"] in gates and gates[x["gate_no"]] is None:
            gates[x["gate_no"]]=x
    html='''<div class="kicker">LEITSTAND</div><h1 class="page-title">Wareneingang · Tore 8–12</h1>
    <div class="toolbar"><a class="small-btn" href="/containers">+ Container</a><a class="small-btn" href="/tasks">Aufträge</a>
    <a class="small-btn" href="/quality">Probleme / Quarantäne</a></div><div class="leit-grid">'''
    for gate in range(8,13):
        x=gates[gate]
        if not x:
            html += f'''<div class="leit-gate"><div class="muted">TOR</div><div class="big-status">Tor {gate}</div>
            <span class="pill green">FREI</span><p class="muted">Kein aktiver Container</p></div>'''
            continue
        item_stats=c.execute("SELECT COALESCE(SUM(article_count),0) units,COALESCE(SUM(cartons),0) cartons FROM items WHERE container_id=?",(x["id"],)).fetchone()
        carriers=c.execute("SELECT COUNT(*) total,SUM(CASE WHEN status='eingelagert' THEN 1 ELSE 0 END) stored FROM load_carriers WHERE container_id=?",(x["id"],)).fetchone()
        total=carriers["total"] or 0
        stored=carriers["stored"] or 0
        progress=round(stored/total*100) if total else 0
        cls="yellow" if x["status"]=="verspätet" else "green"
        html += f'''<div class="leit-gate"><div class="muted">TOR {gate}</div><div class="big-status">{x["container_no"]}</div>
        <span class="pill {cls}">{x["status"].upper()}</span>
        <p><b>{item_stats["cartons"]}</b> Kartons · <b>{item_stats["units"]}</b> Artikel</p>
        <p><b>{stored}/{total}</b> Ladungsträger eingelagert</p>
        <div class="progress"><span style="width:{progress}%"></span></div>
        <a class="yellow-link" href="/container/{x["id"]}">Container öffnen →</a><br>
        <a class="yellow-link" href="/container/{x["id"]}/check">Wareneingang prüfen →</a></div>'''
    c.close()
    html += '</div>'
    return page(html,"dashboard")


@app.route("/container/<int:cid>/check", methods=["GET","POST"])
def inbound_check(cid):
    c=con()
    cont=c.execute("SELECT * FROM containers WHERE id=?",(cid,)).fetchone()
    if not cont:
        c.close(); return redirect("/containers")
    if request.method=="POST":
        expected=max(0,int(request.form.get("expected_cartons",0)))
        received=max(0,int(request.form.get("received_cartons",0)))
        damaged=max(0,int(request.form.get("damaged_units",0)))
        missing=max(0,int(request.form.get("missing_units",0)))
        c.execute("INSERT INTO inbound_checks(container_id,article_no,expected_cartons,received_cartons,damaged_units,missing_units,note,created_at) VALUES(?,?,?,?,?,?,?,?)",
                  (cid,request.form["article_no"].strip(),expected,received,damaged,missing,request.form.get("note","").strip(),datetime.now().isoformat(timespec="minutes")))
        c.commit(); c.close(); return redirect(f"/container/{cid}/check")
    checks=c.execute("SELECT * FROM inbound_checks WHERE container_id=? ORDER BY id DESC",(cid,)).fetchall()
    c.close()
    html=f'''<div class="kicker">WARENEINGANGSKONTROLLE</div><h1 class="page-title">{cont["container_no"]}</h1>
    <div class="card"><form method="post">
    Artikelnummer<input name="article_no" required>
    <div class="row"><div>Soll-Kartons<input type="number" min="0" name="expected_cartons" required></div>
    <div>Ist-Kartons<input type="number" min="0" name="received_cartons" required></div></div>
    <div class="row"><div>Beschädigte Artikel<input type="number" min="0" name="damaged_units" value="0"></div>
    <div>Fehlende Artikel<input type="number" min="0" name="missing_units" value="0"></div></div>
    Notiz<input name="note" placeholder="Schaden, Fehlmenge, falsche Ware …">
    <button>Prüfung speichern</button></form></div>
    <div class="card"><table><tr><th>Zeit</th><th>Artikel</th><th>Soll</th><th>Ist</th><th>Schaden</th><th>Fehlt</th><th>Notiz</th></tr>'''
    for x in checks:
        html += f'<tr><td>{x["created_at"]}</td><td>{x["article_no"]}</td><td>{x["expected_cartons"]}</td><td>{x["received_cartons"]}</td><td>{x["damaged_units"]}</td><td>{x["missing_units"]}</td><td>{x["note"] or "–"}</td></tr>'
    html += '</table></div>'
    return page(html,"containers")


@app.route("/tasks", methods=["GET","POST"])
def tasks_page():
    c=con()
    if request.method=="POST":
        c.execute("INSERT INTO tasks(title,task_type,priority,carrier_no,from_slot,to_slot,note,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                  (request.form["title"].strip(),request.form["task_type"],request.form["priority"],request.form.get("carrier_no","").strip(),
                   request.form.get("from_slot","").strip(),request.form.get("to_slot","").strip(),request.form.get("note","").strip(),
                   "offen",datetime.now().isoformat(timespec="minutes")))
        c.commit(); c.close(); return redirect("/tasks")
    rows=c.execute("SELECT * FROM tasks ORDER BY CASE priority WHEN 'Dringend' THEN 0 WHEN 'Hoch' THEN 1 ELSE 2 END,id DESC").fetchall()
    c.close()
    html='''<div class="kicker">ARBEITSAUFTRÄGE</div><h1 class="page-title">Aufgaben</h1>
    <div class="card"><form method="post">Titel<input name="title" required>
    <div class="row"><div>Typ<select name="task_type"><option>Umlagerung</option><option>Auslagerung</option><option>Inventur</option><option>Problemprüfung</option><option>Allgemein</option></select></div>
    <div>Priorität<select name="priority"><option>Normal</option><option>Hoch</option><option>Dringend</option></select></div></div>
    <div class="row"><div>Ladungsträger<input name="carrier_no"></div><div>Von<input name="from_slot" placeholder="22/1/82"></div></div>
    Nach<input name="to_slot" placeholder="15/3/42">Notiz<input name="note"><button>Auftrag erstellen</button></form></div>
    <div class="card"><table><tr><th>Priorität</th><th>Auftrag</th><th>Träger</th><th>Von</th><th>Nach</th><th>Status</th><th></th></tr>'''
    for x in rows:
        pcls="red" if x["priority"]=="Dringend" else ("yellow" if x["priority"]=="Hoch" else "green")
        html += f'<tr><td><span class="pill {pcls}">{x["priority"]}</span></td><td><b>{x["title"]}</b><br><span class="muted">{x["task_type"]}</span></td><td>{x["carrier_no"] or "–"}</td><td>{x["from_slot"] or "–"}</td><td>{x["to_slot"] or "–"}</td><td>{x["status"]}</td><td>'
        if x["status"]=="offen":
            html += f'<form method="post" action="/task/{x["id"]}/done"><button class="small-btn">Erledigt ✓</button></form>'
        html += '</td></tr>'
    html += '</table></div>'
    return page(html,"dashboard")


@app.route("/task/<int:tid>/done", methods=["POST"])
def task_done(tid):
    c=con()
    c.execute("UPDATE tasks SET status='erledigt',completed_at=? WHERE id=?",(datetime.now().isoformat(timespec="minutes"),tid))
    c.commit(); c.close()
    return redirect("/tasks")


@app.route("/inventory", methods=["GET","POST"])
def inventory():
    msg=""
    if request.method=="POST":
        code=request.form.get("slot_code","").strip()
        scanned=request.form.get("carrier_no","").strip()
        parsed=parse_slot(code)
        if not parsed:
            msg="Ungültiger Lagerplatz."
        else:
            r,l,p=parsed
            c=con()
            slot=c.execute("SELECT * FROM warehouse_slots WHERE rack=? AND level=? AND position=?",(r,l,p)).fetchone()
            expected=(slot["load_carrier_no"] or "") if slot else ""
            result="OK" if expected==scanned else "DIFFERENZ"
            c.execute("INSERT INTO inventory_checks(slot_code,expected_carrier,scanned_carrier,result,created_at) VALUES(?,?,?,?,?)",
                      (code,expected,scanned,result,datetime.now().isoformat(timespec="minutes")))
            c.commit(); c.close()
            msg=f'{result}: System = {expected or "LEER"}, Scan = {scanned or "LEER"}'
    c=con()
    rows=c.execute("SELECT * FROM inventory_checks ORDER BY id DESC LIMIT 100").fetchall()
    c.close()
    html='''<div class="kicker">INVENTUR</div><h1 class="page-title">Inventur per Scan</h1>
    <div class="scanbox"><form method="post">Lagerplatz scannen<input class="scan-input" name="slot_code" required placeholder="22/1/82">
    Ladungsträger scannen <span class="muted">(leer lassen, wenn Platz leer ist)</span><input class="scan-input" name="carrier_no">
    <button>Soll / Ist vergleichen</button></form></div>'''
    if msg:
        cls="ok" if msg.startswith("OK") else "danger"
        html += f'<div class="notice"><b class="{cls}">{msg}</b></div>'
    html += '<div class="card"><table><tr><th>Zeit</th><th>Platz</th><th>Soll</th><th>Ist</th><th>Ergebnis</th></tr>'
    for x in rows:
        cls="ok" if x["result"]=="OK" else "danger"
        html += f'<tr><td>{x["created_at"]}</td><td>{x["slot_code"]}</td><td>{x["expected_carrier"] or "LEER"}</td><td>{x["scanned_carrier"] or "LEER"}</td><td class="{cls}"><b>{x["result"]}</b></td></tr>'
    html += '</table></div>'
    return page(html,"warehouse")


@app.route("/slot-admin", methods=["GET","POST"])
def slot_admin():
    msg=""
    c=con()
    if request.method=="POST":
        code=request.form.get("slot_code","").strip()
        parsed=parse_slot(code)
        if not parsed:
            msg="Ungültiger Lagerplatz."
        else:
            r,l,p=parsed
            action=request.form.get("action")
            slot=c.execute("SELECT * FROM warehouse_slots WHERE rack=? AND level=? AND position=?",(r,l,p)).fetchone()
            if action=="block":
                if slot["load_carrier_id"]:
                    msg="Belegten Platz zuerst umlagern oder auslagern."
                else:
                    c.execute("UPDATE warehouse_slots SET slot_status='gesperrt',block_reason=? WHERE rack=? AND level=? AND position=?",
                              (request.form.get("reason","").strip() or "Gesperrt",r,l,p))
                    c.commit(); msg=f"{code} wurde gesperrt."
            else:
                c.execute("UPDATE warehouse_slots SET slot_status=CASE WHEN load_carrier_id IS NULL THEN 'frei' ELSE 'belegt' END,block_reason=NULL WHERE rack=? AND level=? AND position=?",(r,l,p))
                c.commit(); msg=f"{code} wurde freigegeben."
    blocked=c.execute("SELECT * FROM warehouse_slots WHERE slot_status='gesperrt' ORDER BY rack,level,position").fetchall()
    c.close()
    html='''<div class="kicker">SPERRPLÄTZE</div><h1 class="page-title">Lagerplätze sperren</h1>
    <div class="card"><form method="post">Lagerplatz<input class="scan-input" name="slot_code" required placeholder="22/1/82">
    Grund<input name="reason" placeholder="Regalschaden, Reparatur, Inventur …">
    <div class="row"><button name="action" value="block">Platz sperren</button><button name="action" value="release">Platz freigeben</button></div></form></div>'''
    if msg: html += f'<div class="notice">{msg}</div>'
    html += '<div class="card"><h2>Aktuell gesperrt</h2><table><tr><th>Platz</th><th>Grund</th></tr>'
    for s in blocked:
        html += f'<tr><td><b>{s["rack"]}/{s["level"]}/{s["position"]}</b></td><td>{s["block_reason"] or "–"}</td></tr>'
    html += '</table></div>'
    return page(html,"warehouse")


@app.route("/carrier/<int:lid>/quality", methods=["POST"])
def carrier_quality(lid):
    c=con()
    status=request.form.get("quality_status","frei")
    note=request.form.get("quality_note","").strip()
    c.execute("UPDATE load_carriers SET quality_status=?,quality_note=? WHERE id=?",(status,note,lid))
    lt=c.execute("SELECT * FROM load_carriers WHERE id=?",(lid,)).fetchone()
    if lt:
        c.execute("INSERT INTO movements(load_carrier_id,carrier_no,movement_type,created_at) VALUES(?,?,?,?)",
                  (lid,lt["carrier_no"],f"Qualität: {status}",datetime.now().isoformat(timespec="minutes")))
    c.commit(); c.close()
    return redirect(f"/carrier/{lid}")


@app.route("/quality")
def quality():
    c=con()
    rows=c.execute("SELECT * FROM load_carriers WHERE quality_status!='frei' ORDER BY id DESC").fetchall()
    c.close()
    html='''<div class="kicker">QUALITÄT</div><h1 class="page-title">Quarantäne & Sperrbestand</h1>
    <div class="card"><table><tr><th>Träger</th><th>Artikel</th><th>Menge</th><th>Status</th><th>Notiz</th></tr>'''
    for x in rows:
        html += f'<tr><td><a style="color:white" href="/carrier/{x["id"]}">{x["carrier_no"]}</a></td><td>{x["article_no"] or "–"}</td><td>{x["quantity"]}</td><td><span class="pill yellow">{x["quality_status"]}</span></td><td>{x["quality_note"] or "–"}</td></tr>'
    html += '</table></div>'
    return page(html,"carriers")


@app.route("/sync", methods=["GET","POST"])
def sync_page():
    c=con()
    if request.method=="POST":
        c.execute("INSERT INTO sage_sync_queue(entity_type,entity_id,action,payload,status,created_at) VALUES(?,?,?,?,?,?)",
                  (request.form["entity_type"],request.form["entity_id"].strip(),request.form["action"],
                   request.form.get("payload",""),"wartet",datetime.now().isoformat(timespec="minutes")))
        c.commit(); c.close(); return redirect("/sync")
    rows=c.execute("SELECT * FROM sage_sync_queue ORDER BY id DESC LIMIT 200").fetchall()
    c.close()
    html='''<div class="kicker">SAGE</div><h1 class="page-title">Sage-Synchronisation</h1>
    <div class="notice"><b>Test-/Vorbereitungsmodus.</b><br><span class="muted">Hier sammeln wir Buchungen für Sage. Die echte Verbindung zum Sage-Testserver wird aktiviert, sobald Sage-Version/API/ODBC und Testzugang feststehen.</span></div>
    <div class="card"><form method="post"><div class="row"><div>Objekt<select name="entity_type"><option>Artikel</option><option>Ladungsträger</option><option>Lagerbewegung</option><option>Wareneingang</option></select></div>
    <div>Aktion<select name="action"><option>CREATE</option><option>UPDATE</option><option>POST</option></select></div></div>
    ID / Nummer<input name="entity_id" required>Test-Payload<input name="payload"><button>In Sync-Warteschlange</button></form></div>
    <div class="card"><table><tr><th>Zeit</th><th>Objekt</th><th>ID</th><th>Aktion</th><th>Status</th><th>Fehler</th></tr>'''
    for x in rows:
        cls="green" if x["status"]=="synced" else ("red" if x["status"]=="fehler" else "yellow")
        html += f'<tr><td>{x["created_at"]}</td><td>{x["entity_type"]}</td><td>{x["entity_id"]}</td><td>{x["action"]}</td><td><span class="pill {cls}">{x["status"]}</span></td><td>{x["error_text"] or "–"}</td></tr>'
    html += '</table></div>'
    return page(html,"dashboard")


@app.route("/reports")
def reports():
    c=con(); period=request.args.get('period','30')
    try: days=max(1,min(3650,int(period)))
    except: days=30
    since=(datetime.now()-timedelta(days=days)).isoformat(timespec='minutes')
    moves=c.execute("""SELECT m.*,COALESCE(m.article_no,lc.article_no,'–') ano,COALESCE(NULLIF(m.quantity,0),lc.quantity,0) qty,COALESCE(lc.article_name,'') aname FROM movements m LEFT JOIN load_carriers lc ON lc.id=m.load_carrier_id WHERE m.created_at>=? ORDER BY m.created_at DESC""",(since,)).fetchall()
    inbound=[x for x in moves if 'Einlagerung' in x['movement_type']]; outbound=[x for x in moves if 'Auslagerung' in x['movement_type']]
    in_qty=sum(int(x['qty'] or 0) for x in inbound); out_qty=sum(int(x['qty'] or 0) for x in outbound)
    by={}
    for x in moves:
        no=x['ano']; d=by.setdefault(no,{'name':x['aname'],'in':0,'out':0})
        if 'Einlagerung' in x['movement_type']: d['in']+=int(x['qty'] or 0)
        if 'Auslagerung' in x['movement_type']: d['out']+=int(x['qty'] or 0)
    c.close(); trs=''.join(f"<tr><td>{no}</td><td>{d['name']}</td><td>{d['in']}</td><td>{d['out']}</td><td>{d['in']-d['out']}</td></tr>" for no,d in sorted(by.items())) or '<tr><td colspan="5">Keine Bewegungen im Zeitraum.</td></tr>'
    return page(f"""<div class="kicker">BILANZ</div><h1 class="page-title">Einlagerung ↔ Auslagerung</h1><div class="card"><form><label>Zeitraum</label><select name="period"><option value="1">Heute / 1 Tag</option><option value="7">7 Tage</option><option value="30" {'selected' if days==30 else ''}>30 Tage</option><option value="365">365 Tage</option></select><button>Anzeigen</button></form></div><div class="metric-grid"><div class="metric"><span class="muted">Eingelagert</span><strong>{in_qty}</strong></div><div class="metric"><span class="muted">Ausgelagert</span><strong>{out_qty}</strong></div><div class="metric"><span class="muted">Differenz</span><strong>{in_qty-out_qty}</strong></div><div class="metric"><span class="muted">Bewegungen</span><strong>{len(moves)}</strong></div></div><div class="card"><table><tr><th>Artikel</th><th>Name</th><th>Eingelagert</th><th>Ausgelagert</th><th>Differenz</th></tr>{trs}</table></div>""",'more')

@app.route("/manifest.webmanifest")
def manifest():
    return {
        "name":"LagerPro Lagerverwaltung", "short_name":"LagerPro",
        "id":"/", "start_url":"/", "scope":"/", "display":"standalone",
        "background_color":"#07111f", "theme_color":"#07111f",
        "icons":[{"src":"/app-icon.svg","sizes":"any","type":"image/svg+xml","purpose":"any maskable"}],
    }


@app.route("/app-icon.svg")
def app_icon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
    <rect width="512" height="512" rx="104" fill="#07111f"/>
    <path d="M92 126h328v260H92z" fill="#0d1b2d" stroke="#ffcc00" stroke-width="24"/>
    <path d="M126 178h260M126 244h260M126 310h260M190 126v260M322 126v260" stroke="#ffcc00" stroke-width="16"/>
    <circle cx="388" cy="384" r="66" fill="#35e27a"/><path d="m356 384 22 22 43-49" fill="none" stroke="#07111f" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>"""
    return svg, 200, {"Content-Type":"image/svg+xml", "Cache-Control":"public, max-age=86400"}


@app.route("/sw.js")
def service_worker():
    js="""const CACHE='lagerpro-v39';
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(['/offline','/manifest.webmanifest','/app-icon.svg'])));self.skipWaiting();});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key)))));self.clients.claim();});
self.addEventListener('fetch',event=>{if(event.request.method==='GET'&&event.request.mode==='navigate'){event.respondWith(fetch(event.request).catch(()=>caches.match('/offline')));}});"""
    return js, 200, {"Content-Type":"application/javascript"}


@app.route("/offline")
def offline():
    return page('<div class="kicker">OFFLINE</div><h1 class="page-title">Keine Verbindung</h1><div class="notice">LagerPro benötigt für sichere, aktuelle Lagerbuchungen eine Verbindung zum Server. Bitte Netzwerk prüfen und danach neu laden.</div>','more')


@app.route("/api/health")
def health():
    c=con(); c.execute("SELECT 1").fetchone(); c.close()
    return {"ok":True,"database":True,"database_backend":database_backend(),"version":"V39"}



@app.route("/camera")
def camera_scan():
    html = r"""
    <div class="kicker">KAMERA-SCAN · TEST</div>
    <h1 class="page-title">Ladungsträger & Lagerplatz per Foto</h1>

    <div class="notice">
      <b>Für eure Etiketten angepasst:</b> <code>LD…</code> = Artikelnummer, numerischer Barcode = Ladungsträgernummer,
      „Bezeichnung“ = Artikelname, „Menge“ = Stückzahl und <code>HRL;22;3;37</code> = Lagerplatz <code>22/3/37</code>.
      <br><span class="muted">Artikelnummer, Artikelbezeichnung und Lagerplatz werden automatisch in die Felder übernommen. Fehlende Artikel werden nach der Bestätigung automatisch im Artikelstamm angelegt.</span>
    </div>

    <div class="camera-grid">
      <div class="camera-card">
        <h2>1 · Ladungsträger-Etikett</h2>
        <p class="muted">Fotografiere das Etikett so, dass Trägernummer, Artikelnummer und Artikelname lesbar sind.</p>
        <div class="camera-actions">
          <label class="small-btn" for="carrierPhoto">📷 Etikett fotografieren</label>
          <button type="button" class="small-btn" onclick="resetCarrier()">Zurücksetzen</button>
        </div>
        <input class="camera-file" id="carrierPhoto" type="file" accept="image/*" capture="environment">
        <img id="carrierPreview" class="camera-preview">
        <div id="carrierStatus" class="camera-status">Noch kein Foto.</div>

        <div class="detect-grid">
          <div class="camera-result">Ladungsträgernummer
            <input class="scan-input" id="carrierValue" placeholder="z. B. LT123456">
          </div>
          <div class="camera-result">Artikelnummer
            <input class="scan-input" id="articleNoValue" placeholder="Artikelnummer">
          </div>
        </div>
        <div class="camera-result">Artikelbezeichnung
          <input class="scan-input" id="articleNameValue" placeholder="Artikelname">
        </div>
        <div class="camera-result">Menge auf Ladungsträger
          <input class="scan-input" id="quantityValue" type="number" min="0" placeholder="z. B. 10">
        </div>
      </div>

      <div class="camera-card">
        <h2>2 · Lagerplatz</h2>
        <p class="muted">Fotografiere das Lagerplatzschild, z. B. <b>22/1/82</b>.</p>
        <div class="camera-actions">
          <label class="small-btn" for="slotPhoto">📷 Lagerplatz fotografieren</label>
          <button type="button" class="small-btn" onclick="resetSlot()">Zurücksetzen</button>
        </div>
        <input class="camera-file" id="slotPhoto" type="file" accept="image/*" capture="environment">
        <img id="slotPreview" class="camera-preview">
        <div id="slotStatus" class="camera-status">Noch kein Foto.</div>
        <div class="camera-result">Lagerplatz
          <input class="scan-input" id="slotValue" placeholder="22/1/82">
        </div>
      </div>
    </div>

    <div class="card">
      <h2>3 · Automatisch übernehmen</h2>
      <form method="post" action="/camera/confirm" onsubmit="return fillHidden()">
        <input type="hidden" name="carrier_no" id="carrierHidden">
        <input type="hidden" name="article_no" id="articleNoHidden">
        <input type="hidden" name="article_name" id="articleNameHidden">
        <input type="hidden" name="quantity" id="quantityHidden">
        <input type="hidden" name="slot_code" id="slotHidden">
        <button type="submit">Erkannte Daten automatisch übernehmen</button>
      </form>
    </div>

    <script nonce=""" + g.csp_nonce + r"""" src="https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js"></script>
    <script nonce=""" + g.csp_nonce + r"""">
    function cleanLine(s){return (s||"").replace(/\s+/g," ").trim();}

    // Lagerplatzschild bei euch z. B. "HH · HRL;22;3;37".
    // Daraus wird automatisch unser internes Format "22/3/37".
    function extractSlot(text){
      let m=text.match(/HRL\s*[:;,\-]?\s*([1-9]|[12][0-9]|30)\s*[;\/\-]\s*([1-4])\s*[;\/\-]\s*([1-9]|[1-7][0-9]|8[0-3])/i);
      if(!m) m=text.match(/\b([1-9]|[12][0-9]|30)\s*[;\/\-]\s*([1-4])\s*[;\/\-]\s*([1-9]|[1-7][0-9]|8[0-3])\b/);
      return m?`${m[1]}/${m[2]}/${m[3]}`:"";
    }

    // Eure echten Etiketten:
    // Artikelnummer: Code im Format LD......, z. B. LD660807
    // Ladungsträger: rein numerischer Code, z. B. 735100200
    function extractArticleNo(text){
      const compact=(text||"").replace(/\s+/g,"");
      let m=compact.match(/\bLD[A-Z0-9]{5,12}\b/i);
      if(m) return m[0].toUpperCase();
      const lines=text.split(/\n/).map(cleanLine).filter(Boolean);
      for(const line of lines){
        if(/artikel(?:nummer|nr\.?| no\.?)|article(?: number| no\.?)/i.test(line)){
          const p=line.split(/[:#]/);
          if(p.length>1) return cleanLine(p.slice(1).join(":")).replace(/\s+/g,"");
        }
      }
      return "";
    }

    function extractCarrier(text){
      const lines=text.split(/\n/).map(cleanLine).filter(Boolean);
      for(const line of lines){
        if(/ladungstr[aä]ger|tr[aä]ger|load.?carrier/i.test(line)){
          const p=line.split(/[:#]/);
          if(p.length>1) return cleanLine(p.slice(1).join(":")).replace(/\s+/g,"");
        }
      }
      // 8-12 stellige reine Zahl; LD-Code wird vorher als Artikelnummer erkannt.
      const compact=(text||"").replace(/[^\d\n]/g," ");
      const nums=compact.match(/\b\d{8,12}\b/g)||[];
      return nums.length ? nums[nums.length-1] : "";
    }

    function extractArticleName(text){
      const lines=text.split(/\n/).map(cleanLine).filter(Boolean);
      for(let i=0;i<lines.length;i++){
        if(/^Bezeichnung\s*:?$/i.test(lines[i])){
          // Auf euren Labels kann "Bezeichnung:" zweimal vorkommen.
          for(let j=i+1;j<Math.min(lines.length,i+4);j++){
            if(!/^Bezeichnung\s*:?$/i.test(lines[j]) && !/^Menge\s*:/i.test(lines[j])){
              return lines[j];
            }
          }
        }
        if(/^Bezeichnung\s*:/i.test(lines[i])){
          const value=cleanLine(lines[i].replace(/^Bezeichnung\s*:/i,""));
          if(value) return value;
        }
      }
      return "";
    }

    function extractQuantity(text){
      const m=(text||"").match(/Menge\s*:\s*([0-9]+(?:[.,][0-9]+)?)/i);
      if(!m) return "";
      return String(Math.round(parseFloat(m[1].replace(",","."))));
    }

    async function tryBarcodeDetector(file){
      if(!("BarcodeDetector" in window)) return [];
      try{
        const img=await createImageBitmap(file);
        const detector=new BarcodeDetector({formats:["code_128","code_39","ean_13","ean_8","itf"]});
        const found=await detector.detect(img);
        return found.map(x=>(x.rawValue||"").trim()).filter(Boolean);
      }catch(e){ return []; }
    }
    async function runOCR(file,target){
      if(!file)return;
      const status=document.getElementById(target+"Status");
      const preview=document.getElementById(target+"Preview");
      preview.src=URL.createObjectURL(file); preview.style.display="block";
      status.textContent="Foto wird gelesen …";
      try{
        let barcodeValues=[];
        if(target==="carrier"){
          barcodeValues=await tryBarcodeDetector(file);
          // Direkte Barcodes zuerst: LD... = Artikelnummer, reine Zahl = Ladungsträger.
          for(const rawCode of barcodeValues){
            const code=rawCode.replace(/\*/g,"").replace(/\s+/g,"").trim();
            if(/^LD[A-Z0-9]{5,12}$/i.test(code)){
              document.getElementById("articleNoValue").value=code.toUpperCase();
            }else if(/^\d{8,12}$/.test(code)){
              document.getElementById("carrierValue").value=code;
            }
          }
        }

        const result=await Tesseract.recognize(file,"deu+eng",{logger:m=>{
          if(m.status==="recognizing text") status.textContent=`Text wird erkannt … ${Math.round((m.progress||0)*100)} %`;
        }});
        const raw=result.data.text||"";

        if(target==="carrier"){
          const carrier=extractCarrier(raw);
          const ano=extractArticleNo(raw);
          const aname=extractArticleName(raw);
          const qty=extractQuantity(raw);

          if(!document.getElementById("carrierValue").value && carrier) document.getElementById("carrierValue").value=carrier;
          if(!document.getElementById("articleNoValue").value && ano) document.getElementById("articleNoValue").value=ano;
          if(aname) document.getElementById("articleNameValue").value=aname;
          if(qty) document.getElementById("quantityValue").value=qty;

          const any=document.getElementById("carrierValue").value || document.getElementById("articleNoValue").value || aname || qty;
          status.textContent=any
            ? "Barcode/Text erkannt – Artikel, Ladungsträger, Bezeichnung und Menge wurden automatisch eingetragen."
            : "Nicht sicher erkannt – bitte Foto näher und gerade aufnehmen.";
        }else{
          const slot=extractSlot(raw);
          if(slot) document.getElementById("slotValue").value=slot;
          status.textContent=slot
            ? `Lagerplatz ${slot} erkannt und automatisch eingefügt.`
            : "Lagerplatz nicht sicher erkannt. Bitte Schild frontal fotografieren.";
        }
      }catch(e){
        status.textContent="Erkennung fehlgeschlagen. Bitte erneut fotografieren oder manuell eintragen.";
      }
    }
    document.getElementById("carrierPhoto").addEventListener("change",e=>runOCR(e.target.files[0],"carrier"));
    document.getElementById("slotPhoto").addEventListener("change",e=>runOCR(e.target.files[0],"slot"));
    function resetCarrier(){
      carrierPhoto.value="";carrierPreview.style.display="none";carrierStatus.textContent="Noch kein Foto.";
      carrierValue.value="";articleNoValue.value="";articleNameValue.value="";quantityValue.value="";
    }
    function resetSlot(){slotPhoto.value="";slotPreview.style.display="none";slotStatus.textContent="Noch kein Foto.";slotValue.value="";}
    function fillHidden(){
      carrierHidden.value=carrierValue.value.trim();
      articleNoHidden.value=articleNoValue.value.trim();
      articleNameHidden.value=articleNameValue.value.trim();
      quantityHidden.value=quantityValue.value.trim();
      slotHidden.value=slotValue.value.trim();
      if(!carrierHidden.value||!slotHidden.value){alert("Ladungsträger und Lagerplatz müssen vorhanden sein.");return false;}
      return true;
    }
    </script>
    """
    return page(html,"warehouse")


@app.route("/camera/confirm", methods=["POST"])
def camera_confirm():
    carrier_no=request.form.get("carrier_no","").strip()
    article_no=request.form.get("article_no","").strip()
    article_name=request.form.get("article_name","").strip()
    try:
        quantity=max(0,int(float((request.form.get("quantity","0") or "0").replace(",","."))))
    except Exception:
        quantity=0
    slot_code=request.form.get("slot_code","").strip()

    if not carrier_no:
        abort(400, description="Ladungsträgernummer fehlt")

    warnings=[]
    actions=[]
    c=con()

    # Article recognition is now productive: create article master automatically if missing.
    article=None
    if article_no:
        article=c.execute("""
            SELECT *, COALESCE(NULLIF(article_name,''), name, article_no) AS booking_article_name
            FROM articles WHERE article_no=?
        """,(article_no,)).fetchone()
        if not article:
            safe_name=article_name or f"Artikel {article_no}"
            c.execute("""INSERT INTO articles(article_no,name,article_name,pallet_type,cpp,storage_rule,units_per_carton)
                         VALUES(?,?,?,?,?,?,?)""",
                      (article_no,safe_name,safe_name,"Euro",max(1,quantity),"Alle Ebenen",1))
            c.commit()
            article=c.execute("SELECT * FROM articles WHERE article_no=?",(article_no,)).fetchone()
            actions.append(f"Artikel {article_no} wurde automatisch im Artikelstamm angelegt.")
            warnings.append("Neuer Artikel wurde mit Standardwerten angelegt: Euro, alle Ebenen, 1 Artikel/Karton. Bitte Stammdaten später prüfen.")
        elif article_name and (not article["article_name"] or article["article_name"].startswith("Artikel ")):
            c.execute("UPDATE articles SET article_name=? WHERE article_no=?",(article_name,article_no))
            c.commit()
            article=c.execute("SELECT * FROM articles WHERE article_no=?",(article_no,)).fetchone()
            actions.append("Artikelbezeichnung wurde aus dem Foto übernommen.")

    lt=c.execute("SELECT * FROM load_carriers WHERE carrier_no=?",(carrier_no,)).fetchone()
    if not lt:
        # Company-generated carrier number is still respected: we only record the photographed real number.
        c.execute("""INSERT INTO load_carriers(carrier_no,article_no,article_name,quantity,pallet_type,status,created_at)
                     VALUES(?,?,?,?,?,?,?)""",
                  (carrier_no,article_no or None,
                   (article["article_name"] if article else article_name) or None,
                   quantity,(article["pallet_type"] if article else "Euro"),
                   "offen",datetime.now().isoformat(timespec="minutes")))
        c.commit()
        lt=c.execute("SELECT * FROM load_carriers WHERE carrier_no=?",(carrier_no,)).fetchone()
        actions.append(f"Ladungsträger {carrier_no} wurde mit der fotografierten Nummer erfasst.")
    elif article_no:
        # Do not silently overwrite a different existing article assignment.
        if lt["article_no"] and lt["article_no"] != article_no:
            warnings.append(f'ACHTUNG: Ladungsträger ist bereits Artikel {lt["article_no"]} zugeordnet; Foto erkennt {article_no}. Keine automatische Änderung.')
        elif not lt["article_no"]:
            c.execute("""UPDATE load_carriers SET article_no=?,article_name=?,pallet_type=?,quantity=? WHERE id=?""",
                      (article_no,
                       (article["article_name"] if article else article_name),
                       (article["pallet_type"] if article else lt["pallet_type"]),
                       quantity if quantity else lt["quantity"],
                       lt["id"]))
            c.commit()
            lt=c.execute("SELECT * FROM load_carriers WHERE id=?",(lt["id"],)).fetchone()
            actions.append("Erkannter Artikel wurde dem Ladungsträger automatisch zugeordnet.")
        elif lt["article_no"] == article_no and quantity and quantity != lt["quantity"]:
            c.execute("UPDATE load_carriers SET quantity=? WHERE id=?",(quantity,lt["id"]))
            c.commit()
            lt=c.execute("SELECT * FROM load_carriers WHERE id=?",(lt["id"],)).fetchone()
            actions.append(f"Erkannte Menge {quantity} wurde automatisch am Ladungsträger übernommen.")

    parsed=parse_slot(slot_code)
    slot=None
    can_store=False
    if not parsed:
        warnings.append("Lagerplatz konnte nicht gültig erkannt werden. Erwartet wird z. B. 22/1/82.")
    else:
        r,l,p=parsed
        slot=c.execute("SELECT * FROM warehouse_slots WHERE rack=? AND level=? AND position=?",(r,l,p)).fetchone()
        if not slot:
            warnings.append("Lagerplatz existiert nicht.")
        elif slot["slot_status"]=="gesperrt":
            warnings.append(f'Lagerplatz ist gesperrt: {slot["block_reason"] or "kein Grund angegeben"}.')
        elif slot["load_carrier_id"] and slot["load_carrier_id"] != lt["id"]:
            warnings.append(f'Lagerplatz ist bereits durch {slot["load_carrier_no"]} belegt.')
        else:
            can_store=True
            actions.append(f"Lagerplatz {slot_code} wurde automatisch aus dem Foto übernommen.")

    c.close()

    html=f"""
    <div class="kicker">KAMERA-AUTOMATIK</div><h1 class="page-title">Foto erkannt & übernommen</h1>
    <div class="card"><table>
      <tr><th>Feld</th><th>Erkannt / übernommen</th></tr>
      <tr><td>Ladungsträger</td><td><b>{carrier_no or "–"}</b></td></tr>
      <tr><td>Artikelnummer</td><td><b>{article_no or "–"}</b></td></tr>
      <tr><td>Artikel</td><td>{(article["article_name"] if article else article_name) or "–"}</td></tr>
      <tr><td>Menge</td><td><b>{quantity}</b></td></tr>
      <tr><td>Lagerplatz</td><td><b>{slot_code or "–"}</b></td></tr>
    </table></div>
    """
    if actions:
        html += '<div class="card"><h2>Automatisch ausgeführt</h2>'
        for a in actions: html += f'<div class="notice"><b class="ok">✓ {a}</b></div>'
        html += '</div>'
    if warnings:
        html += '<div class="card"><h2 class="warn">Hinweise / Prüfung nötig</h2>'
        for w in warnings: html += f'<div class="notice">{w}</div>'
        html += '</div>'

    # Storage still passes through all normal safety/business-rule checks.
    if can_store:
        html += f"""
        <div class="card">
          <form method="post" action="/store">
            <input type="hidden" name="carrier_no" value="{carrier_no}">
            <input type="hidden" name="slot_code" value="{slot_code}">
            <button>Jetzt mit Lagerregeln einlagern</button>
          </form>
          <p class="muted">Die App prüft dabei weiterhin Sperrplatz, Ebene, Belegung, Qualitätsstatus und Euro/Einweg-Regel.</p>
        </div>
        """
    html += '<div class="card"><a class="yellow-link" href="/camera">← Nächstes Etikett fotografieren</a></div>'
    return page(html,"warehouse")





@app.route("/manual-booking", methods=["GET","POST"])
def manual_booking():
    msg=""
    success=False
    c=con()

    if request.method=="POST":
        article_no=request.form.get("article_no","").strip()
        article_name_input=request.form.get("article_name","").strip()
        slot_code=request.form.get("slot_code","").strip()

        try:
            cartons_on_pallet=max(1,int(float((request.form.get("cartons_on_pallet","1") or "1").replace(",","."))))
        except Exception:
            cartons_on_pallet=1

        if not article_no:
            msg="Bitte eine Artikelnummer eingeben."
        elif not article_name_input:
            msg="Bitte den Artikelnamen eingeben."
        else:
            article=c.execute("""
                SELECT *,
                       COALESCE(NULLIF(article_name,''), NULLIF(name,''), article_no) AS booking_article_name
                FROM articles
                WHERE article_no=?
            """,(article_no,)).fetchone()

            created_new=False

            if not article:
                # Neuer Artikel wird direkt mit den eingegebenen Stammdaten angelegt.
                c.execute("""
                    INSERT INTO articles(
                        article_no,name,article_name,pallet_type,cpp,storage_rule,units_per_carton
                    )
                    VALUES(?,?,?,?,?,?,?)
                """,(
                    article_no,
                    article_name_input,
                    article_name_input,
                    "Euro",
                    cartons_on_pallet,
                    "Alle Ebenen",
                    1
                ))
                c.commit()
                created_new=True
            else:
                # Bei manueller Buchung werden Name und Kartons/Palette direkt
                # auch im Artikelstamm aktualisiert.
                c.execute("""
                    UPDATE articles
                    SET name=?, article_name=?, cpp=?
                    WHERE article_no=?
                """,(
                    article_name_input,
                    article_name_input,
                    cartons_on_pallet,
                    article_no
                ))
                c.commit()

            article=c.execute("""
                SELECT *,
                       COALESCE(NULLIF(article_name,''), NULLIF(name,''), article_no) AS booking_article_name
                FROM articles
                WHERE article_no=?
            """,(article_no,)).fetchone()

            parsed=parse_slot(slot_code)

            if not parsed:
                msg="Lagerplatz ungültig. Format z. B. 22/3/37."
            else:
                r,l,p=parsed
                slot=c.execute(
                    "SELECT * FROM warehouse_slots WHERE rack=? AND level=? AND position=?",
                    (r,l,p)
                ).fetchone()

                if not slot:
                    msg="Lagerplatz existiert nicht."
                elif slot["slot_status"]=="gesperrt":
                    msg=f'Lagerplatz ist gesperrt: {slot["block_reason"] or "kein Grund angegeben"}.'
                elif slot["load_carrier_id"]:
                    msg=f'Der Platz ist bereits durch {slot["load_carrier_no"] or "einen Ladungsträger"} belegt.'
                elif slot["slot_status"] != "frei":
                    msg=f'Der Lagerplatz ist aktuell {slot["slot_status"]} und kann nicht bebucht werden.'
                else:
                    rule=(article["storage_rule"] or "Alle Ebenen")
                    if rule in ("Nur Ebene 1","nur Ebene 1") and l!=1:
                        msg="Dieser Artikel darf nur auf Ebene 1 eingelagert werden."
                    elif rule in ("Nur Ebene 2-4","nur Ebene 2-4") and l==1:
                        msg="Dieser Artikel darf nur auf Ebene 2–4 eingelagert werden."
                    else:
                        neighbors=c.execute("""SELECT pallet_type FROM warehouse_slots
                            WHERE rack=? AND level=? AND position IN (?,?)
                            AND load_carrier_id IS NOT NULL""",(r,l,p-1,p+1)).fetchall()
                        is_euro=(article["pallet_type"] or "Euro")=="Euro"
                        conflict=any(
                            ((n["pallet_type"] or "Euro")=="Euro") != is_euro
                            for n in neighbors
                        )
                        if conflict:
                            msg="Euro und Einweg dürfen nicht direkt nebeneinander stehen."
                            c.rollback()
                            article = None

                    if article is not None and not msg:
                        stamp=datetime.now().strftime("%Y%m%d%H%M%S%f")
                        carrier_no=f"MAN-{r}-{l}-{p}-{stamp[-6:]}"
                        now=datetime.now().isoformat(timespec="minutes")

                        # quantity = Kartons auf dieser Palette / diesem Lagerplatz
                        cur=c.execute(
                            "INSERT INTO load_carriers(carrier_no,article_no,article_name,quantity,pallet_type,status,rack,level,position,created_at,closed_at,stored_at,quality_status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (
                                carrier_no,
                                article["article_no"],
                                article["booking_article_name"],
                                cartons_on_pallet,
                                article["pallet_type"],
                                "eingelagert",
                                r,l,p,now,now,now,"frei"
                            )
                        )
                        lid=cur.lastrowid

                        updated=c.execute(
                            "UPDATE warehouse_slots SET article_no=?,article_name=?,pallet_type=?,quantity=?,occupied_at=?,load_carrier_no=?,load_carrier_id=?,slot_status='belegt' WHERE rack=? AND level=? AND position=? AND load_carrier_id IS NULL AND slot_status='frei'",
                            (
                                article["article_no"],
                                article["booking_article_name"],
                                article["pallet_type"],
                                cartons_on_pallet,
                                now,
                                carrier_no,
                                lid,
                                r,l,p
                            )
                        )

                        if updated.rowcount != 1:
                            c.rollback()
                            msg="Der Lagerplatz wurde gleichzeitig von einem anderen Benutzer belegt. Bitte neu laden."
                            c.close()
                            return page(f'<div class="notice danger">{escape(msg)}</div>',"warehouse"),409

                        c.execute(
                            "INSERT INTO movements(load_carrier_id,carrier_no,movement_type,article_no,quantity,from_slot,to_slot,created_at) VALUES(?,?,?,?,?,?,?,?)",
                            (lid,carrier_no,"Manuelle Einlagerung",article["article_no"],cartons_on_pallet,None,slot_code,now)
                        )

                        c.commit()
                        prefix="Neuer Artikel automatisch im Artikelstamm angelegt. " if created_new else "Artikelstamm automatisch aktualisiert. "
                        msg=prefix + f'{article["article_no"]} - {article["booking_article_name"]}: {cartons_on_pallet} Kartons auf {slot_code} gebucht.'
                        success=True

    selected_slot = (request.form.get("slot_code","") if request.method=="POST" else request.args.get("slot_code","")).strip()

    articles=c.execute("""
        SELECT article_no,
               COALESCE(NULLIF(article_name,''), NULLIF(name,''), article_no) AS article_name,
               COALESCE(cpp,1) AS cpp,
               COALESCE(pallet_type,'Euro') AS pallet_type,
               COALESCE(storage_rule,'Alle Ebenen') AS storage_rule
        FROM articles
        ORDER BY article_name, article_no
        LIMIT 1000
    """).fetchall()
    c.close()

    import json
    article_data = {
        a["article_no"]: {
            "article_name": a["article_name"],
            "cpp": a["cpp"],
            "pallet_type": a["pallet_type"],
            "storage_rule": a["storage_rule"]
        } for a in articles
    }
    article_json = json.dumps(article_data, ensure_ascii=False).replace("</", "<\\/")

    html=f"""<div class="kicker">MANUELLE DIREKTBUCHUNG</div>
    <h1 class="page-title">Artikel auf Lagerplatz buchen</h1>

    <div class="notice">
      <b>Lagerplatz: {selected_slot or 'noch nicht gewählt'}</b><br>
      <span class="muted">
        Wähle einen vorhandenen Artikel direkt aus dem Artikelstamm. Artikelnummer, Name und Kartons pro Palette werden automatisch übernommen.
        Alternativ kannst du weiterhin einen neuen Artikel anlegen.
      </span>
    </div>

    <div class="card">
      <form method="post" id="booking-form">
        <label>Artikel aus Artikelstamm auswählen</label>
        <select class="scan-input" id="article_select">
          <option value="">— Artikel auswählen —</option>"""

    for a in articles:
        html += f'<option value="{a["article_no"]}">{a["article_name"]} · {a["article_no"]} · {a["cpp"]} Kartons/Palette</option>'

    html += f"""</select>
        <div style="margin:8px 0 18px"><span class="muted">Du kannst die Liste öffnen und den gewünschten Artikel direkt anklicken.</span></div>

        <div class="row">
          <div>
            Artikelnummer
            <input class="scan-input" id="article_no" name="article_no" required placeholder="wird bei Auswahl automatisch übernommen">
          </div>
          <div>
            Artikelname
            <input class="scan-input" id="article_name" name="article_name" required placeholder="wird bei Auswahl automatisch übernommen">
          </div>
        </div>

        <div class="row">
          <div>
            Kartons auf Palette
            <input class="scan-input" id="cartons_on_pallet" type="number" min="1" name="cartons_on_pallet" value="1" required>
            <span class="muted">Bei vorhandenem Artikel aus dem Artikelstamm übernommen.</span>
          </div>
          <div>
            Lagerplatz
            <input class="scan-input" name="slot_code" required value="{selected_slot}" placeholder="z. B. 22/3/37">
          </div>
        </div>

        <div id="article_info" class="notice" style="display:none"></div>
        <button>Artikel auf Lagerplatz buchen</button>
      </form>
    </div>

    <div class="card">
      <h2>Neuer Artikel?</h2>
      <p class="muted">Wenn der Artikel noch nicht im Artikelstamm steht, lässt du die Auswahl oben leer und trägst Artikelnummer, Artikelname und Kartons auf Palette manuell ein. Beim Buchen wird der Artikel automatisch angelegt.</p>
    </div>

    <script nonce="{g.csp_nonce}">
      const articles = {article_json};
      const select = document.getElementById('article_select');
      const no = document.getElementById('article_no');
      const name = document.getElementById('article_name');
      const cpp = document.getElementById('cartons_on_pallet');
      const info = document.getElementById('article_info');

      function fillArticle() {{
        const a = articles[select.value];
        if (!a) {{
          info.style.display = 'none';
          return;
        }}
        no.value = select.value;
        name.value = a.article_name || '';
        cpp.value = a.cpp || 1;
        info.innerHTML = '<b>Aus Artikelstamm übernommen:</b> ' +
          (a.pallet_type || 'Euro') + ' · ' + (a.storage_rule || 'Alle Ebenen') +
          ' · ' + (a.cpp || 1) + ' Kartons/Palette';
        info.style.display = 'block';
      }}
      select.addEventListener('change', fillArticle);
    </script>"""

    if msg:
        cls="ok" if success else "danger"
        html += f'<div class="notice"><b class="{cls}">{msg}</b></div>'

    return page(html,"warehouse")


@app.route("/gates")
def gates():
    c = con()
    rows = c.execute("""
    SELECT * FROM containers
    WHERE status!='erledigt'
    AND gate_no BETWEEN 8 AND 12
    """).fetchall()
    c.close()

    gate_data = {item["gate_no"]: item for item in rows}

    html = """
    <div class="kicker">TORE</div>
    <h1 class="page-title">Hallentore 8–12</h1>
    <div class="card">
      <div class="gates">
    """

    for gate in range(8, 13):
        item = gate_data.get(gate)

        if item:
            html += f"""
            <div class="gate">
              <div class="gate-number">Tor {gate}</div>
              <span class="dot green"></span><br>
              <b>{item["container_no"]}</b><br>
              {item["status"]}
            </div>
            """
        else:
            html += f"""
            <div class="gate">
              <div class="gate-number">Tor {gate}</div>
              <span class="dot gray"></span><br>
              <span class="muted">Frei</span>
            </div>
            """

    html += "</div></div>"
    return page(html, "gates")

# ================= V30 COMPLETE MODULES =================
def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def audit(action, entity_type="", entity_id="", before=None, after=None, note=""):
    try:
        c=con(); c.execute("INSERT INTO audit_log(user_id,username,action,entity_type,entity_id,before_json,after_json,note,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(session.get('user_id'),session.get('username','system'),action,entity_type,str(entity_id),json.dumps(before,ensure_ascii=False) if before else None,json.dumps(after,ensure_ascii=False) if after else None,note,now_iso())); c.commit(); c.close()
    except Exception:
        logging.exception("Audit-Eintrag konnte nicht geschrieben werden")

def role_allowed(*roles):
    return session.get('role') in roles

@app.before_request
def security_gate():
    if request.endpoint in {'login','setup_admin','health','manifest','service_worker','app_icon','offline','static'}:
        return
    c=con(); count=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    timeout_row=c.execute("SELECT setting_value FROM app_settings WHERE setting_key='auto_logout'").fetchone()
    c.close()
    if count==0: return redirect('/setup')
    if not session.get('user_id'): return redirect('/login?next='+request.path)
    last=session.get('last_seen')
    if last:
        try:
            timeout_hours=max(1,min(24,int(timeout_row[0]))) if timeout_row else 8
            if datetime.now()-datetime.fromisoformat(last)>timedelta(hours=timeout_hours): session.clear(); return redirect('/login')
        except (TypeError, ValueError):
            session.clear(); return redirect('/login')
    session['last_seen']=now_iso()
    allowed = {
        'users_page': {'Admin'}, 'settings_page': {'Admin'}, 'backup_page': {'Admin'},
        'audit_page': {'Admin','Lagerleitung'}, 'email_log_page': {'Admin','Lagerleitung'},
        'purchasing_page': {'Admin','Lagerleitung'}, 'reports': {'Admin','Lagerleitung'},
        'control_center': {'Admin','Lagerleitung'}, 'slot_admin': {'Admin','Lagerleitung'},
        'sync_page': {'Admin','Lagerleitung'}, 'quality': {'Admin','Lagerleitung'},
        'carrier_quality': {'Admin','Lagerleitung'},
    }
    if request.endpoint in allowed and session.get('role') not in allowed[request.endpoint]:
        abort(403)

@app.route('/setup',methods=['GET','POST'])
def setup_admin():
    c=con(); n=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if n: c.close(); return redirect('/login')
    msg=''
    if request.method=='POST':
        u=request.form.get('username','').strip(); pw=request.form.get('password',''); name=request.form.get('full_name','').strip() or u
        if len(u)<3 or len(pw)<8: msg='Benutzername min. 3 Zeichen, Passwort min. 8 Zeichen.'
        else:
            c.execute("INSERT INTO users(username,password_hash,full_name,role,created_at) VALUES(?,?,?,?,?)",(u,generate_password_hash(pw),name,'Admin',now_iso())); c.commit(); c.close(); return redirect('/login')
    c.close(); return page(f'<div class="kicker">ERSTEINRICHTUNG</div><h1 class="page-title">Administrator anlegen</h1><div class="card"><p class="danger">{msg}</p><form method="post"><input name="full_name" placeholder="Name" required><input name="username" placeholder="Benutzername" required><input type="password" name="password" placeholder="Passwort" required><button>Admin erstellen</button></form></div>','more')

@app.route('/login',methods=['GET','POST'])
def login():
    msg=''
    if request.method=='POST':
        u=request.form.get('username','').strip(); pw=request.form.get('password',''); c=con(); x=c.execute("SELECT * FROM users WHERE username=?",(u,)).fetchone(); locked=False
        if x and x['locked_until']:
            try: locked=datetime.fromisoformat(x['locked_until'])>datetime.now()
            except (TypeError, ValueError):
                locked=True
        if x and x['active'] and not locked and check_password_hash(x['password_hash'],pw):
            c.execute("UPDATE users SET failed_logins=0,locked_until=NULL WHERE id=?",(x['id'],)); c.commit(); c.close(); session.clear(); session.update(user_id=x['id'],username=x['username'],role=x['role'],last_seen=now_iso(),csrf_token=secrets.token_urlsafe(32)); audit('Login','user',x['id']); nxt=request.args.get('next') or '/'; return redirect(nxt if nxt.startswith('/') and not nxt.startswith('//') else '/')
        if x:
            f=(x['failed_logins'] or 0)+1; until=(datetime.now()+timedelta(minutes=15)).isoformat(timespec='seconds') if f>=5 else None; c.execute("UPDATE users SET failed_logins=?,locked_until=? WHERE id=?",(f,until,x['id'])); c.commit()
        c.close(); msg='Anmeldung fehlgeschlagen.'
    return page(f'<div class="kicker">LOGIN</div><h1 class="page-title">LagerPro anmelden</h1><div class="card"><p class="danger">{msg}</p><form method="post"><input name="username" placeholder="Benutzername" required><input type="password" name="password" placeholder="Passwort" required><button>Anmelden</button></form></div>','more')

@app.route('/logout',methods=['POST'])
def logout():
    audit('Logout','user',session.get('user_id')); session.clear(); return redirect('/login')

@app.route('/users',methods=['GET','POST'])
def users_page():
    if not role_allowed('Admin'): return page('<div class="card">Keine Berechtigung.</div>','more'),403
    c=con(); msg=''
    if request.method=='POST':
        try:
            u=request.form['username'].strip(); role=request.form.get('role','Mitarbeiter')
            if role not in {'Mitarbeiter','Lagerleitung','Admin'} or len(u)<3 or len(request.form['password'])<10:
                raise ValueError('Ungültige Benutzerdaten')
            c.execute("INSERT INTO users(username,password_hash,full_name,role,created_at) VALUES(?,?,?,?,?)",(u,generate_password_hash(request.form['password']),request.form.get('full_name',u).strip(),role,now_iso())); c.commit(); audit('Benutzer angelegt','user',u,after={'role':role}); msg='Benutzer angelegt.'
        except Exception:
            c.rollback(); msg='Benutzer konnte nicht angelegt werden. Benutzername eventuell bereits vergeben.'
    rows=c.execute("SELECT * FROM users ORDER BY username").fetchall(); c.close(); trs=''.join(f"<tr><td>{r['username']}</td><td>{r['full_name']}</td><td>{r['role']}</td><td>{'aktiv' if r['active'] else 'inaktiv'}</td></tr>" for r in rows)
    return page(f'<div class="kicker">ADMIN · ZUGANGSVERWALTUNG</div><h1 class="page-title">Benutzer hinzufügen</h1><div class="notice">Ohne Anmeldung sehen Benutzer ausschließlich die Login-Seite. Nach erfolgreicher Anmeldung erhalten sie Zugriff entsprechend ihrer Rolle. Nur Administratoren können diesen Bereich öffnen.</div><div class="card"><h2>Neuen Benutzer anlegen</h2><p>{escape(msg)}</p><form method="post"><div class="row"><input name="full_name" maxlength="120" placeholder="Name" required><input name="username" minlength="3" maxlength="80" placeholder="Benutzername" required></div><div class="row"><input type="password" name="password" minlength="10" placeholder="Startpasswort" required><select name="role"><option>Mitarbeiter</option><option>Lagerleitung</option><option>Admin</option></select></div><button>Benutzer hinzufügen</button></form></div><div class="card"><h2>Vorhandene Benutzer</h2><table><tr><th>Benutzer</th><th>Name</th><th>Rolle</th><th>Status</th></tr>{trs}</table></div>','users')

@app.route('/more')
def more_page():
    links=[('/stock','Bestände'),('/purchasing','Einkauf / Nachbestellen'),('/reports','Bilanz / Berichte'),('/batch-booking','Mehrfach-Einlagerung'),('/reservations','Reservierungen'),('/optimizer','Optimierungsassistent'),('/simulation','Lager-Simulation'),('/handover','Schichtübergabe'),('/notifications','Frühwarnsystem')]
    if role_allowed('Admin'):
        links += [('/audit','Audit-Historie'),('/backup','Backups'),('/settings','Einstellungen'),('/users','Benutzerverwaltung')]
    cards=''.join(f'<a class="action-card" href="{u}"><b>{t}</b><span class="muted">Öffnen</span></a>' for u,t in links)
    cards += '<form method="post" action="/logout"><button class="action-card" style="width:100%;text-align:left"><b>Abmelden</b><span class="muted">Sicher beenden</span></button></form>'
    return page(f'<div class="kicker">ERWEITERUNGEN</div><h1 class="page-title">LagerPro Complete</h1><div class="action-grid">{cards}</div>','more')

@app.route('/stock')
def stock_page():
    q=request.args.get('q','').strip(); c=con(); sql="SELECT article_no,article_name,COUNT(*) pallets,SUM(quantity) qty,GROUP_CONCAT(rack||'-'||level||'-'||position) slots FROM load_carriers WHERE status!='ausgelagert' AND rack IS NOT NULL"; args=[]
    if q: sql+=" AND (article_no LIKE ? OR article_name LIKE ?)"; args=[f'%{q}%',f'%{q}%']
    sql+=" GROUP BY article_no,article_name ORDER BY article_name"; rows=c.execute(sql,args).fetchall(); c.close(); trs=''.join(f"<tr><td>{r['article_no']}</td><td>{r['article_name']}</td><td>{r['pallets']}</td><td>{r['qty'] or 0}</td><td>{r['slots'] or ''}</td></tr>" for r in rows)
    return page(f'<div class="kicker">BESTAND</div><h1 class="page-title">Bestände & Teilpaletten</h1><div class="card"><form><input name="q" value="{q}" placeholder="Artikelnummer oder Name"><button>Suchen</button></form></div><div class="card"><table><tr><th>Nr.</th><th>Artikel</th><th>Paletten</th><th>Kartons</th><th>Plätze</th></tr>{trs}</table></div>','more')

@app.route('/batch-booking',methods=['GET','POST'])
def batch_booking():
    c=con()
    msg=''
    try:
        gang=max(1,min(30,int(request.values.get('gang',1) or 1)))
    except (TypeError,ValueError):
        gang=1
    try:
        level=max(1,min(4,int(request.values.get('level',1) or 1)))
    except (TypeError,ValueError):
        level=1
    maxpos=89 if gang<=7 else 83

    if request.method=='POST':
        selected_slots=request.form.getlist('slots')
        ano=request.form.get('article_no','').strip()
        aname=request.form.get('article_name','').strip()
        try:
            qty=max(1,int(request.form.get('quantity') or 1))
        except (TypeError,ValueError):
            qty=1
        ptype=request.form.get('pallet_type','Euro').strip() or 'Euro'
        booked=[]
        skipped=[]

        article=c.execute("SELECT * FROM articles WHERE article_no=?",(ano,)).fetchone() if ano else None
        if article:
            if not aname:
                try:
                    aname=(article['article_name'] or article['name'] or ano)
                except Exception:
                    aname=ano
            storage_rule=article['storage_rule'] or 'Alle Ebenen'
            # Bestehenden Palettentyp aus dem Stamm verwenden, falls im Formular nichts Sinnvolles ankommt.
            if ptype not in ('Euro','Einweg'):
                ptype=article['pallet_type'] or 'Euro'
        else:
            storage_rule='Alle Ebenen'
            if ano:
                if not aname:
                    aname=ano
                c.execute("INSERT INTO articles(article_no,name,article_name,pallet_type,cpp,storage_rule) VALUES(?,?,?,?,?,?)",
                          (ano,aname,aname,ptype,qty,storage_rule))

        if not ano:
            msg='Bitte einen Artikel auswählen oder eine Artikelnummer eingeben.'
        elif not selected_slots:
            msg='Keine Lagerplätze ausgewählt.'
        else:
            for raw_code in selected_slots:
                parsed=parse_slot(raw_code)
                if not parsed:
                    skipped.append(f'{raw_code}: ungültiger Lagerplatz')
                    continue
                r,l,p=parsed
                # POST darf nur die aktuell gewählte Reihe buchen.
                if r != gang or l != level:
                    skipped.append(f'{raw_code}: gehört nicht zur gewählten Reihe')
                    continue
                sl=c.execute("SELECT * FROM warehouse_slots WHERE rack=? AND level=? AND position=?",(r,l,p)).fetchone()
                if not sl:
                    skipped.append(f'{raw_code}: Lagerplatz fehlt')
                    continue
                if sl['slot_status']!='frei' or sl['load_carrier_id']:
                    skipped.append(f'{raw_code}: nicht mehr frei')
                    continue
                if storage_rule=='Nur Ebene 1' and l!=1:
                    skipped.append(f'{raw_code}: Artikel nur Ebene 1')
                    continue
                if storage_rule=='Nur Ebene 2-4' and l==1:
                    skipped.append(f'{raw_code}: Artikel nur Ebene 2-4')
                    continue

                # Euro und Einweg dürfen nicht direkt nebeneinander stehen.
                neighbors=c.execute("""SELECT pallet_type FROM warehouse_slots
                    WHERE rack=? AND level=? AND position IN (?,?) AND load_carrier_id IS NOT NULL""",
                    (r,l,p-1,p+1)).fetchall()
                this_euro=(ptype=='Euro')
                conflict=any((n['pallet_type']=='Euro') != this_euro for n in neighbors if n['pallet_type'])
                if conflict:
                    skipped.append(f'{raw_code}: Euro/Einweg-Nachbarschaft nicht erlaubt')
                    continue

                try:
                    now=now_iso()
                    no='MAN-'+datetime.now().strftime('%y%m%d%H%M%S%f')[-16:]
                    cur=c.execute("""INSERT INTO load_carriers(
                        carrier_no,article_no,article_name,quantity,pallet_type,status,rack,level,position,created_at,stored_at
                    ) VALUES(?,?,?,?,?,'eingelagert',?,?,?,?,?)""",
                    (no,ano,aname,qty,ptype,r,l,p,now,now))
                    lid=cur.lastrowid
                    updated=c.execute("""UPDATE warehouse_slots SET
                        load_carrier_id=?,load_carrier_no=?,article_no=?,article_name=?,pallet_type=?,quantity=?,
                        slot_status='belegt',occupied_at=?
                        WHERE rack=? AND level=? AND position=? AND load_carrier_id IS NULL AND slot_status='frei'""",
                        (lid,no,ano,aname,ptype,qty,now,r,l,p))
                    if updated.rowcount != 1:
                        c.execute("DELETE FROM load_carriers WHERE id=?",(lid,))
                        skipped.append(f'{raw_code}: wurde gleichzeitig belegt')
                        continue
                    standard_code=f'{r}/{l}/{p}'
                    c.execute("INSERT INTO movements(load_carrier_id,carrier_no,movement_type,article_no,quantity,to_slot,created_at) VALUES(?,?,?,?,?,?,?)",
                              (lid,no,'Mehrfach-Einlagerung',ano,qty,standard_code,now))
                    booked.append(standard_code)
                except Exception as exc:
                    skipped.append(f'{raw_code}: Buchungsfehler {type(exc).__name__}')

            c.commit()
            audit('Mehrfach-Einlagerung','article',ano,after={'slots':booked,'skipped':len(skipped)})
            msg=f'{len(booked)} Paletten eingelagert.'
            if skipped:
                msg += f' {len(skipped)} Platz/Plätze wurden übersprungen.'

    slots=c.execute("SELECT * FROM warehouse_slots WHERE rack=? AND level=? AND position<=? ORDER BY position",
                    (gang,level,maxpos)).fetchall()
    arts=c.execute("SELECT article_no,COALESCE(article_name,name) n,pallet_type,cpp FROM articles ORDER BY n LIMIT 1000").fetchall()
    c.close()

    checks=''.join(
        f"<label class='slot {'free' if x['slot_status']=='frei' and not x['load_carrier_id'] else 'occupied'}'>"
        f"<input type='checkbox' name='slots' value='{gang}/{level}/{x['position']}' "
        f"{'disabled' if x['slot_status']!='frei' or x['load_carrier_id'] else ''}>"
        f"<b>{gang}-{level}-{x['position']}</b><span>{x['slot_status']}</span></label>"
        for x in slots
    )
    opts=''.join(f"<option value='{a['article_no']}'>{a['n']} · {a['article_no']}</option>" for a in arts)
    return page(
        f'<div class="kicker">MEHRFACHAUSWAHL</div>'
        f'<h1 class="page-title">Gleichen Artikel schneller einlagern</h1>'
        f'<div class="notice">Mehrere freie Plätze auswählen. Jede Palette wird weiterhin als eigener Ladungsträger mit eigener Historie gebucht.</div>'
        f'<div class="card"><form method="get"><div class="row">'
        f'<input type="number" name="gang" min="1" max="30" value="{gang}">'
        f'<input type="number" name="level" min="1" max="4" value="{level}"></div>'
        f'<button>Reihe anzeigen</button></form></div>'
        f'<form method="post"><input type="hidden" name="gang" value="{gang}">'
        f'<input type="hidden" name="level" value="{level}"><div class="slot-grid">{checks}</div>'
        f'<div class="card"><p class="ok">{msg}</p><label>Artikelstamm</label>'
        f'<input list="arts" name="article_no" placeholder="Artikelnummer" required><datalist id="arts">{opts}</datalist>'
        f'<input name="article_name" placeholder="Artikelname (bei neuem Artikel)">'
        f'<div class="row"><input type="number" name="quantity" min="1" value="1">'
        f'<select name="pallet_type"><option>Euro</option><option>Einweg</option></select></div>'
        f'<button>Ausgewählte Plätze buchen</button></div></form>',
        'warehouse'
    )

@app.route('/reservations',methods=['GET','POST'])
def reservations_page():
    c=con(); msg=''
    if request.method=='POST':
        code=request.form.get('slot_code','').strip()
        try:
            r,l,p=parse_slot(code); sl=c.execute("SELECT * FROM warehouse_slots WHERE rack=? AND level=? AND position=?",(r,l,p)).fetchone()
            if sl and sl['slot_status']=='frei' and not sl['load_carrier_id']:
                c.execute("INSERT INTO slot_reservations(slot_code,article_no,reason,reserved_by,created_at) VALUES(?,?,?,?,?)",(code,request.form.get('article_no'),request.form.get('reason'),session.get('username'),now_iso())); c.execute("UPDATE warehouse_slots SET slot_status='reserviert' WHERE rack=? AND level=? AND position=?",(r,l,p)); c.commit(); audit('Reservierung','slot',code); msg='Platz reserviert.'
            else: msg='Platz nicht frei.'
        except Exception: msg='Ungültiger Platz.'
    rows=c.execute("SELECT * FROM slot_reservations WHERE status='aktiv' ORDER BY id DESC").fetchall(); c.close(); trs=''.join(f"<tr><td>{x['slot_code']}</td><td>{x['article_no'] or '-'}</td><td>{x['reason'] or '-'}</td><td>{x['reserved_by']}</td></tr>" for x in rows)
    return page(f'<div class="kicker">RESERVIERUNG</div><h1 class="page-title">Plätze für kommende Ware reservieren</h1><div class="card"><p>{msg}</p><form method="post"><input name="slot_code" placeholder="Gang-Ebene-Position" required><input name="article_no" placeholder="Artikel optional"><input name="reason" placeholder="Grund / Container"><button>Reservieren</button></form></div><div class="card"><table>{trs}</table></div>','more')

@app.route('/optimizer')
def optimizer_page():
    c=con(); rows=c.execute("SELECT article_no,article_name,COUNT(DISTINCT rack) gangs,COUNT(*) pallets,GROUP_CONCAT(rack||'-'||level||'-'||position) slots FROM load_carriers WHERE status!='ausgelagert' AND rack IS NOT NULL GROUP BY article_no,article_name HAVING COUNT(DISTINCT rack)>1 ORDER BY gangs DESC LIMIT 50").fetchall(); c.close(); trs=''.join(f"<tr><td>{x['article_no']}</td><td>{x['article_name']}</td><td>{x['pallets']}</td><td>{x['gangs']}</td><td>{x['slots']}</td></tr>" for x in rows)
    return page(f'<div class="kicker">INTELLIGENZ</div><h1 class="page-title">Optimierungsassistent</h1><div class="notice">Findet verteilte Artikel. Das System schlägt vor; Umlagerungen werden nicht automatisch ausgeführt.</div><div class="card"><table><tr><th>Nr.</th><th>Artikel</th><th>Paletten</th><th>Gänge</th><th>Plätze</th></tr>{trs}</table></div>','more')

@app.route('/simulation',methods=['GET','POST'])
def simulation_page():
    incoming=int(request.form.get('pallets') or 0) if request.method=='POST' else 0; c=con(); free=c.execute("SELECT COUNT(*) FROM warehouse_slots WHERE slot_status='frei' AND load_carrier_id IS NULL").fetchone()[0]; total=c.execute("SELECT COUNT(*) FROM warehouse_slots").fetchone()[0]; c.close(); remain=free-incoming
    return page(f'<div class="kicker">SIMULATION</div><h1 class="page-title">Was passiert bei neuem Wareneingang?</h1><div class="cards"><div class="card"><div class="number">{total}</div>Plätze</div><div class="card"><div class="number">{free}</div>frei</div></div><div class="card"><form method="post"><input type="number" name="pallets" min="0" value="{incoming}" placeholder="kommende Paletten"><button>Simulieren</button></form><h2 class="{"ok" if remain>=0 else "danger"}">{remain} Plätze verbleiben</h2></div>','more')

@app.route('/handover')
def handover_page():
    c=con(); tasks=c.execute("SELECT * FROM tasks WHERE status='offen' ORDER BY id DESC LIMIT 25").fetchall(); cont=c.execute("SELECT * FROM containers WHERE status!='erledigt' ORDER BY id DESC LIMIT 20").fetchall(); blocks=c.execute("SELECT rack,level,position,block_reason FROM warehouse_slots WHERE slot_status='gesperrt' LIMIT 30").fetchall(); c.close(); a=''.join(f"<li>{x['priority']} · {x['title']}</li>" for x in tasks) or '<li>Keine</li>'; b=''.join(f"<li>{x['container_no']} · Tor {x['gate_no'] or '-'} · {x['status']}</li>" for x in cont) or '<li>Keine</li>'; d=''.join(f"<li>{x['rack']}-{x['level']}-{x['position']} · {x['block_reason'] or 'gesperrt'}</li>" for x in blocks) or '<li>Keine</li>'
    return page(f'<div class="kicker">SCHICHT</div><h1 class="page-title">Schichtübergabe</h1><div class="two"><div class="card"><h2>Offene Aufgaben</h2><ul>{a}</ul></div><div class="card"><h2>Container</h2><ul>{b}</ul></div></div><div class="card"><h2>Sperrplätze</h2><ul>{d}</ul></div>','more')

@app.route('/notifications')
def notifications_page():
    c=con(); blocked=c.execute("SELECT COUNT(*) FROM warehouse_slots WHERE slot_status='gesperrt'").fetchone()[0]; quarantine=c.execute("SELECT COUNT(*) FROM load_carriers WHERE quality_status='quarantaene'").fetchone()[0]; delayed=c.execute("SELECT COUNT(*) FROM containers WHERE status='verspätet'").fetchone()[0]; tasks=c.execute("SELECT COUNT(*) FROM tasks WHERE status='offen'").fetchone()[0]; total=c.execute("SELECT COUNT(*) FROM warehouse_slots").fetchone()[0]; occ=c.execute("SELECT COUNT(*) FROM warehouse_slots WHERE load_carrier_id IS NOT NULL").fetchone()[0]; c.close(); pct=round(100*occ/total) if total else 0
    return page(f'<div class="kicker">FRÜHWARNSYSTEM</div><h1 class="page-title">Hinweise</h1><div class="notice danger">{blocked} gesperrte Plätze</div><div class="notice warn">{quarantine} Quarantäne-Träger</div><div class="notice warn">{delayed} verspätete Container</div><div class="notice">{tasks} offene Aufgaben</div><div class="notice">Lagerauslastung {pct}%</div>','more')

@app.route('/audit')
def audit_page():
    if not role_allowed('Admin','Lagerleitung'): return page('<div class="card">Keine Berechtigung.</div>','more'),403
    c=con(); rows=c.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 300").fetchall(); c.close(); trs=''.join(f"<tr><td>{x['created_at']}</td><td>{x['username']}</td><td>{x['action']}</td><td>{x['entity_type']} {x['entity_id']}</td></tr>" for x in rows)
    return page(f'<div class="kicker">SICHERHEIT</div><h1 class="page-title">Audit-Historie</h1><div class="card"><table><tr><th>Zeit</th><th>Benutzer</th><th>Aktion</th><th>Objekt</th></tr>{trs}</table></div>','more')

@app.route('/backup',methods=['GET','POST'])
def backup_page():
    if not role_allowed('Admin'): return page('<div class="card">Nur Admin.</div>','more'),403
    if database_backend() == 'postgresql':
        return page('<div class="kicker">BACKUP</div><h1 class="page-title">Datensicherung</h1><div class="notice"><b>PostgreSQL aktiv.</b> Sicherungen werden im Railway-PostgreSQL-Dienst verwaltet. Aktiviere dort tägliche Backups und führe vor dem Firmenstart eine Wiederherstellungsprobe durch.</div>','more')
    c=con(); msg=''
    if request.method=='POST':
        folder=os.path.join(os.path.dirname(DB),'backups'); os.makedirs(folder,exist_ok=True); fn='lagerpro_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.db'
        try: shutil.copy2(DB,os.path.join(folder,fn)); c.execute("INSERT INTO backup_log(filename,status,created_at) VALUES(?,?,?)",(fn,'ok',now_iso())); c.commit(); audit('Backup','system',fn); msg='Backup erstellt: '+fn
        except Exception as e: msg='Fehler: '+str(e)
    rows=c.execute("SELECT * FROM backup_log ORDER BY id DESC LIMIT 20").fetchall(); c.close(); trs=''.join(f"<tr><td>{x['created_at']}</td><td>{x['filename']}</td><td>{x['status']}</td></tr>" for x in rows)
    return page(f'<div class="kicker">BACKUP</div><h1 class="page-title">Datensicherung</h1><div class="card"><p>{msg}</p><form method="post"><button>Backup jetzt erstellen</button></form></div><div class="card"><table>{trs}</table></div>','more')


@app.route('/container/<int:cid>/finish',methods=['POST'])
def finish_container(cid):
    c=con(); cont=c.execute("SELECT * FROM containers WHERE id=?",(cid,)).fetchone()
    if not cont: c.close(); return redirect('/containers')
    finished=now_iso()
    claimed=c.execute("""UPDATE containers SET status='erledigt',unload_finished_at=?,
        completion_email_claimed_at=?,completion_email_error=NULL
        WHERE id=? AND completion_email_claimed_at IS NULL AND completion_email_sent_at IS NULL""",
        (finished,finished,cid))
    c.commit(); c.close()
    if claimed.rowcount != 1:
        return redirect(f'/container/{cid}')
    who=session.get('username') or 'Unbekannt'; gate=cont['gate_no'] or '–'
    ok=send_system_email('container_fertig',f"Container fertig: {cont['container_no']} · Tor {gate}",f"Container {cont['container_no']} wurde fertig gebucht.\nTor: {gate}\nFertig am: {finished}\nGebucht von: {who}\n\nLagerPro")
    c=con()
    if ok:
        c.execute("UPDATE containers SET completion_email_sent_at=? WHERE id=?",(now_iso(),cid))
    else:
        c.execute("UPDATE containers SET completion_email_claimed_at=NULL,completion_email_error=? WHERE id=?",('Versand fehlgeschlagen – erneuter Abschluss versucht den Versand erneut',cid))
    c.commit(); c.close()
    audit('Container fertig','container',cid,after={'status':'erledigt','gate':gate})
    return redirect(f'/container/{cid}')

@app.route('/purchasing',methods=['GET','POST'])
def purchasing_page():
    c=con(); msg=''
    if request.method=='POST':
        no=request.form.get('article_no','').strip()
        try: mn=max(0,int(request.form.get('min_stock') or 0)); target=max(mn,int(request.form.get('target_stock') or mn))
        except: mn=target=0
        c.execute("UPDATE articles SET min_stock=?,target_stock=? WHERE article_no=?",(mn,target,no)); c.commit(); msg='Bestandsgrenzen gespeichert.'
    rows=c.execute("SELECT article_no,COALESCE(article_name,name,article_no) n,min_stock,target_stock FROM articles ORDER BY n").fetchall()
    data=[]
    for a in rows:
        stock=article_stock(c,a['article_no']); target=max(int(a['target_stock'] or 0),int(a['min_stock'] or 0)); data.append((a,stock,max(0,target-stock)))
    c.close(); check_reorders()
    trs=''.join(f"<tr><td>{a['article_no']}</td><td>{a['n']}</td><td><b>{stock}</b></td><td>{a['min_stock']}</td><td>{a['target_stock']}</td><td>{suggested}</td><td><span class='pill {'red' if a['min_stock'] and stock<=a['min_stock'] else 'green'}'>{'NACHBESTELLEN' if a['min_stock'] and stock<=a['min_stock'] else 'OK'}</span></td><td><form method='post'><input type='hidden' name='article_no' value='{a['article_no']}'><input style='width:80px' type='number' min='0' name='min_stock' value='{a['min_stock']}'><input style='width:80px' type='number' min='0' name='target_stock' value='{a['target_stock']}'><button class='small-btn'>Speichern</button></form></td></tr>" for a,stock,suggested in data)
    return page(f"""<div class="kicker">EINKAUF</div><h1 class="page-title">Nachbestellungen</h1><div class="notice">Sobald der Bestand den Mindestbestand erreicht oder unterschreitet, wird einmalig eine E-Mail ausgelöst. Erst wenn der Bestand wieder darüber liegt und später erneut fällt, entsteht eine neue Meldung.</div><div class="card"><p class="ok">{msg}</p><table><tr><th>Nr.</th><th>Artikel</th><th>Bestand</th><th>Minimum</th><th>Soll</th><th>Vorschlag</th><th>Status</th><th>Grenzen ändern</th></tr>{trs}</table></div>""",'more')

@app.route('/settings/test-email',methods=['POST'])
def test_email():
    if not role_allowed('Admin'): return page('<div class="card">Nur Admin.</div>','more'),403
    ok=send_system_email('test', 'LagerPro Test-Mail', 'Die SMTP-Konfiguration von LagerPro funktioniert.\n\nZeitpunkt: '+now_iso())
    c=con(); row=c.execute("SELECT * FROM email_log WHERE event_type='test' ORDER BY id DESC LIMIT 1").fetchone(); c.close()
    if ok: msg='<div class="notice ok"><b>Test-Mail wurde versendet.</b></div>'
    else: msg='<div class="notice danger"><b>Test-Mail fehlgeschlagen.</b><br>'+((row['error_text'] if row else None) or 'Unbekannter SMTP-Fehler')+'</div>'
    return page('<div class="kicker">E-MAIL TEST</div><h1 class="page-title">SMTP-Diagnose</h1>'+msg+'<p><a class="small-btn" href="/settings">Zurück zu Einstellungen</a></p>','more')

@app.route('/email-log')
def email_log_page():
    if not role_allowed('Admin','Lagerleitung'): return page('<div class="card">Keine Berechtigung.</div>','more'),403
    c=con(); rows=c.execute("SELECT * FROM email_log ORDER BY id DESC LIMIT 200").fetchall(); c.close()
    trs=''.join(f"<tr><td>{x['created_at']}</td><td>{x['event_type']}</td><td>{x['recipient'] or '–'}</td><td>{x['subject']}</td><td>{x['status']}</td><td>{x['error_text'] or '–'}</td></tr>" for x in rows)
    return page(f'<div class="kicker">E-MAIL</div><h1 class="page-title">Versandprotokoll</h1><div class="card"><table><tr><th>Zeit</th><th>Ereignis</th><th>Empfänger</th><th>Betreff</th><th>Status</th><th>Fehler</th></tr>{trs}</table></div>','more')

@app.route('/settings',methods=['GET','POST'])
def settings_page():
    if not role_allowed('Admin'): return page('<div class="card">Nur Admin.</div>','more'),403
    c=con(); defaults={'company_name':'LagerPro','auto_logout':'8','four_eyes_threshold':'10','notification_emails':'','smtp_host':'','smtp_port':'587','smtp_user':'','smtp_sender':'','smtp_starttls':'1','smtp_ssl':'0'}
    if request.method=='POST':
        for k in defaults:
            val=request.form.get(k,defaults[k])
            c.execute("INSERT INTO app_settings(setting_key,setting_value,updated_at) VALUES(?,?,?) ON CONFLICT(setting_key) DO UPDATE SET setting_value=excluded.setting_value,updated_at=excluded.updated_at",(k,val,now_iso()))
        c.commit(); audit('Einstellungen geändert','system')
    vals=defaults.copy(); vals.update({x['setting_key']:x['setting_value'] for x in c.execute("SELECT * FROM app_settings")}); c.close()
    vals.update({k:v for k,v in get_settings().items() if k in defaults})
    checked_tls='checked' if vals['smtp_starttls']=='1' else ''; checked_ssl='checked' if vals['smtp_ssl']=='1' else ''
    return page(f"""<div class="kicker">ADMIN</div><h1 class="page-title">Einstellungen & E-Mail</h1>
    <div class="card"><form method="post"><label>Systemname</label><input name="company_name" value="{vals['company_name']}"><label>Auto-Logout Stunden</label><input type="number" name="auto_logout" value="{vals['auto_logout']}"><label>Vier-Augen-Schwelle</label><input type="number" name="four_eyes_threshold" value="{vals['four_eyes_threshold']}">
    <h2>E-Mail-Benachrichtigungen</h2><label>Empfänger (Vorgesetzter / Einkauf; mehrere mit Komma)</label><input name="notification_emails" value="{vals['notification_emails']}" placeholder="vorgesetzter@firma.de, einkauf@firma.de">
    <div class="row"><div><label>SMTP-Server</label><input name="smtp_host" value="{vals['smtp_host']}" placeholder="smtp.office365.com"></div><div><label>Port</label><input type="number" name="smtp_port" value="{vals['smtp_port']}"></div></div>
    <div class="row"><div><label>SMTP-Benutzer</label><input name="smtp_user" value="{vals['smtp_user']}"></div><div><label>Absender</label><input name="smtp_sender" value="{vals['smtp_sender']}"></div></div>
    <div class="notice">Das SMTP-Passwort wird aus der geschützten Railway-Variable <code>SMTP_PASSWORD</code> gelesen und niemals in der Lagerdatenbank oder im Browser angezeigt.</div>
    <label><input type="checkbox" name="smtp_starttls" value="1" {checked_tls}> STARTTLS verwenden</label><label><input type="checkbox" name="smtp_ssl" value="1" {checked_ssl}> Direktes SSL verwenden</label><button type="submit">Speichern</button></form></div>
    <div class="card"><h2>SMTP-Verbindung testen</h2><p>Speichere die Einstellungen zuerst. Anschließend sendet LagerPro eine Testmail an die oben eingetragenen Empfänger.</p>
    <form method="post" action="/settings/test-email"><button type="submit">Testmail jetzt senden</button></form>
    <p style="margin-top:12px"><a class="small-btn" href="/email-log">E-Mail-Protokoll öffnen</a></p></div>""",'more')

# ================= ENDE V30 MODULES =================

init_db()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",  # nosec B104
        port=int(os.environ.get("PORT", "8080"))
    )
