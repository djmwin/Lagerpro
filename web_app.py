from flask import Flask, request, redirect
import sqlite3, os, math
from datetime import datetime

app = Flask(__name__)
DB = os.environ.get("LAGERPRO_DB", os.path.join(os.path.dirname(__file__), "lagerpro.db"))
LOGO_DATA = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAb8AAAG/CAMAAAD/zSlAAAAA8FBMVEX///8lHUL8vRr///0AAAC6uL+KiZAlHUQAACQnH0UAABqqqbOoprL7uw/2xUYAACb49/kfFj4AAAj99dr///jg3+Tzx1EXDDrw8PIAACAAAB3Y1tsAACsmIj+/vsMOADH889Fyb4BxcHrOy9J6eoT2wDhTUGELADUaGS84M07utxj++s1kYnD40noAABb52YlERFKdmqQTEyQSCDH+/dj//e1APlEAADD57LxPTllaWGNOTlKIhpQZFTEXEjQuLEPt6vUkIzNBQEX235XuxVxgYGM2NkH34qQqKjIPDhj21HAhIR9RS2RcWXJFP1ogHyQnirSlAAAgAElEQVR4nO2dC3vaOLOATQ0I42SxSVyb4OAGU2i6lC8sG2jYXJpe0p492/3+/785GskG2xpjQ0jTPmfep9uy4IussUaj0WikaQRBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEARBEDujP3cBCILIQs3y14bk90ugWw6G99zlIkrSq7YUGh+d5y4WUZL+gim4g+cuFVESq80qCq3ecxeLKIWu9dqq+FjH0sl8+RXQtStbld9oqZH8fgV0zfnGmJERnzGpPXfBiFLomnmb6f74/9o3Ho3+fhHqbrbvq1QWZ6Q+fwm4+lzaUmZJAZ7UuPxIgL8CZqBaL+6QBu+/CFbdV+W3qFvPXS6iHM4dMnqYmc9dLKIMvIfjg3fF+2LPw+cuGVEKXesvsmM/3v19ee5yEaXQdevGVuXH1SfZnr8AfIQQVlX1yf6gwfsvAZdff4SMHpbPXTCiFLrm/VedOjLaNXK+/CwIL0rkSkFkYt4yo5LpAFnVIvn9LIDo9OgvRIL9rO+Ti282fI6CEiibG5JzoQ7ejQkN3n8aLMvznF7tYDo1a6HnZb1iNVvt/uybX8L3aUn2eMWfpc+I9aTldM3B+K5Zrbab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"

def con():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

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

    add_col("articles", "units_per_carton INTEGER NOT NULL DEFAULT 1")
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

    # Backfill article_count for old container positions if present.
    c.execute("""
        UPDATE items
        SET article_count = cartons * COALESCE(NULLIF(units_per_carton,0),1)
        WHERE COALESCE(article_count,0)=0
    """)

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
</style>
"""

def bottom_nav(active):
    pages = [
        ("/","⌂","Dashboard","dashboard"),
        ("/articles","◈","Artikel","articles"),
        ("/containers","▣","Container","containers"),
        ("/carriers","▤","Träger","carriers"),
        ("/warehouse","▦","Lager","warehouse"),
        ("/gates","▥","Tore","gates"),
        ("/archive","◷","Archiv","archive"),
    ]
    html = '<div class="bottom-nav">'
    for url, icon, text, key in pages:
        cls = "active" if active == key else ""
        html += f'<a href="{url}" class="{cls}"><span class="icon">{icon}</span>{text}</a>'
    return html + "</div>"

def page(content, active="dashboard"):
    now = datetime.now()
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lagerprozess</title>
{STYLE}
</head>
<body>
<header class="topbar">
  <div class="top-inner">
    <div class="logo-wrap">
      <img src="{LOGO_DATA}" alt="drive MEDICAL">
    </div>
    <div class="profile">
      <div class="avatar">MB</div>
      <div class="datetime">{now.strftime("%d.%m.%Y")}<br>{now.strftime("%H:%M")} Uhr</div>
    </div>
  </div>
</header>
<main class="main">{content}</main>
{bottom_nav(active)}
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
    c.close()

    free = total_places - occupied
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

    <section class="cards">
      <div class="card">
        <div class="card-title">Gesamtstellplätze</div>
        <div class="number">{total_places}</div>
        <div class="muted">30 Regale × 4 Ebenen × 83 Plätze</div>
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
        c.execute("""
        INSERT INTO articles(article_no,name,pallet_type,cpp,storage_rule,units_per_carton)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(article_no) DO UPDATE SET
          name=excluded.name,
          pallet_type=excluded.pallet_type,
          storage_rule=excluded.storage_rule,
          units_per_carton=excluded.units_per_carton
        """, (
            request.form["no"].strip(),
            request.form["name"].strip(),
            request.form["ptype"],
            1,
            request.form["rule"],
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
      <tr><th>Nr.</th><th>Name</th><th>Artikel/Karton</th><th>Palette</th><th>Regel</th></tr>
    """
    for x in rows:
        html += f"""<tr><td>{x["article_no"]}</td><td>{x["name"]}</td>
        <td><b>{x["units_per_carton"]}</b></td><td>{x["pallet_type"]}</td><td>{x["storage_rule"]}</td></tr>"""
    html += "</table></div>"
    return page(html, "articles")


@app.route("/containers", methods=["GET", "POST"])
def containers():
    c = con()
    if request.method == "POST":
        gate = int(request.form["gate"]) if request.form.get("gate") else None
        c.execute("""INSERT INTO containers(container_no,gate_no,status,created_at)
                     VALUES(?,?,?,?)""",
                  (request.form["no"].strip(), gate, request.form["status"],
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
            except sqlite3.IntegrityError:
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
                except sqlite3.IntegrityError:
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
    return page(html,"carriers")


def parse_slot(code):
    try:
        r,l,p=[int(x) for x in code.strip().split("/")]
        if 1<=r<=30 and 1<=l<=4 and 1<=p<=83:
            return r,l,p
    except Exception:
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
            if slot["load_carrier_id"] and slot["load_carrier_id"] != lt["id"]:
                msg="Dieser Lagerplatz ist bereits belegt."
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
                                     quantity=NULL,container_id=NULL,occupied_at=NULL,load_carrier_no=NULL,load_carrier_id=NULL
                                     WHERE load_carrier_id=?""",(lt["id"],))
                    now=datetime.now().isoformat(timespec="minutes")
                    c.execute("""UPDATE warehouse_slots SET article_no=?,article_name=?,pallet_type=?,quantity=?,
                                 container_id=?,occupied_at=?,load_carrier_no=?,load_carrier_id=?
                                 WHERE rack=? AND level=? AND position=?""",
                              (lt["article_no"],lt["article_name"],lt["pallet_type"],lt["quantity"],
                               lt["container_id"],now,lt["carrier_no"],lt["id"],r,l,p))
                    c.execute("""UPDATE load_carriers SET rack=?,level=?,position=?,status='eingelagert',stored_at=?
                                 WHERE id=?""",(r,l,p,now,lt["id"]))
                    c.execute("""INSERT INTO movements(load_carrier_id,carrier_no,movement_type,from_slot,to_slot,created_at)
                                 VALUES(?,?,?,?,?,?)""",(lt["id"],lt["carrier_no"],"Einlagerung/Umlagerung",old,slot_code,now))
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


@app.route("/warehouse")
def warehouse():
    try:r=max(1,min(30,int(request.args.get("rack",1))))
    except:r=1
    try:l=max(1,min(4,int(request.args.get("level",1))))
    except:l=1
    c=con()
    slots=c.execute("SELECT * FROM warehouse_slots WHERE rack=? AND level=? ORDER BY position",(r,l)).fetchall()
    occ=c.execute("SELECT COUNT(*) FROM warehouse_slots WHERE rack=? AND level=? AND load_carrier_id IS NOT NULL",(r,l)).fetchone()[0]
    c.close()
    ropts="".join(f'<option value="{x}" {"selected" if x==r else ""}>Regal {x}</option>' for x in range(1,31))
    lopts="".join(f'<option value="{x}" {"selected" if x==l else ""}>Ebene {x}</option>' for x in range(1,5))
    html=f"""<div class="kicker">LAGER</div><h1 class="page-title">9.960 Stellplätze</h1>
    <div class="card"><form method="get" class="warehouse-toolbar">
      <div>Regal<select name="rack" onchange="this.form.submit()">{ropts}</select></div>
      <div>Ebene<select name="level" onchange="this.form.submit()">{lopts}</select></div>
    </form><div class="row"><div><span class="muted">Belegt</span><div class="number">{occ}</div></div>
    <div><span class="muted">Frei</span><div class="number">{83-occ}</div></div></div></div>
    <div class="card"><div class="section-head"><h2>Regal {r} · Ebene {l}</h2><span class="muted">83 Plätze</span></div><div class="slot-grid">"""
    for s in slots:
        code=f'{r}/{l}/{s["position"]}'
        if s["load_carrier_id"]:
            html += f"""<a class="slot occupied" href="/carrier/{s["load_carrier_id"]}">
              <div class="slot-code">{code}</div><div class="slot-info">{s["load_carrier_no"]}<br>{s["article_no"]}</div>
              <div class="slot-state">BELEGT</div></a>"""
        else:
            html += f"""<div class="slot free"><div class="slot-code">{code}</div>
              <div class="slot-info">Freier Lagerplatz</div><div class="slot-state">FREI</div></div>"""
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

init_db()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080"))
    )
