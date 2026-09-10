from flask import Flask, request, redirect, render_template_string
import sqlite3, os, math
from datetime import datetime

app=Flask(__name__)
DB=os.environ.get("LAGERPRO_DB",os.path.join(os.path.dirname(__file__),"lagerpro.db"))

def con():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def calc(q,cpp):
    q=int(q); cpp=max(1,int(cpp)); return q//cpp,q%cpp,math.ceil(q/cpp) if q else 0
def init():
    c=con(); c.executescript('''
CREATE TABLE IF NOT EXISTS articles(id INTEGER PRIMARY KEY,article_no TEXT UNIQUE,name TEXT,pallet_type TEXT,cpp INTEGER,storage_rule TEXT);
CREATE TABLE IF NOT EXISTS containers(id INTEGER PRIMARY KEY,container_no TEXT,gate_no INTEGER,status TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY,container_id INTEGER,article_no TEXT,name TEXT,cartons INTEGER,cpp INTEGER,pallet_type TEXT);
'''); c.commit(); c.close()

STYLE='''<style>*{box-sizing:border-box}body{margin:0;background:#0d1117;color:#e6edf3;font-family:-apple-system,Segoe UI,sans-serif}header{padding:20px;background:#161b22}.brand{font-size:25px;font-weight:800}.muted{color:#8b949e}nav{display:flex;gap:8px;overflow:auto;padding:12px}nav a,.btn,button{background:#238636;color:white;text-decoration:none;border:0;border-radius:10px;padding:11px 14px;font-weight:700}nav a{background:#21262d;white-space:nowrap}main{max-width:1100px;margin:auto;padding:16px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.card{background:#161b22;border:1px solid #30363d;border-radius:16px;padding:16px;margin-bottom:14px}.kpi{font-size:28px;font-weight:800}.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}input,select{width:100%;padding:12px;margin:5px 0 10px;background:#0d1117;color:white;border:1px solid #30363d;border-radius:10px}table{width:100%;border-collapse:collapse}td,th{padding:10px;border-bottom:1px solid #30363d;text-align:left}.gates{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}.gate{text-align:center;padding:18px;background:#0d1117;border-radius:14px;border:1px solid #30363d}.badge{background:#30363d;border-radius:20px;padding:5px 9px}@media(max-width:700px){.grid{grid-template-columns:1fr 1fr}.row{grid-template-columns:1fr}.gates{grid-template-columns:1fr 1fr}table{display:block;overflow:auto}}</style>'''
def page(body):
    return render_template_string('<meta name="viewport" content="width=device-width,initial-scale=1">'+STYLE+'<header><div class="brand">ð¦ LagerPro</div><div class="muted">Mobile Lager- & Containerverwaltung</div></header><nav><a href="/">Dashboard</a><a href="/articles">Artikel</a><a href="/containers">Container</a><a href="/gates">Tore 8â12</a></nav><main>'+body+'</main>')

@app.route("/")
def home():
    c=con(); ac=c.execute("SELECT COUNT(*) n FROM articles").fetchone()["n"]; cs=c.execute("SELECT * FROM containers WHERE status!='erledigt'").fetchall(); its=c.execute("SELECT * FROM items").fetchall(); c.close()
    cartons=sum(x["cartons"] for x in its); places=sum(calc(x["cartons"],x["cpp"])[2] for x in its)
    b=f'<div class="grid"><div class="card"><span class="muted">Artikel</span><div class="kpi">{ac}</div></div><div class="card"><span class="muted">Offene Container</span><div class="kpi">{len(cs)}</div></div><div class="card"><span class="muted">Kartons</span><div class="kpi">{cartons}</div></div><div class="card"><span class="muted">PalettenplÃ¤tze</span><div class="kpi">{places}</div></div></div><div class="card"><h2>Aktive Container</h2>'
    b+=''.join(f'<p><a class="btn" href="/container/{x["id"]}">{x["container_no"]}</a> &nbsp; Tor {x["gate_no"] or "â"} Â· <span class="badge">{x["status"]}</span></p>' for x in cs) or '<p class="muted">Noch keine Container.</p>'
    return page(b+'</div>')

@app.route("/articles",methods=["GET","POST"])
def articles():
    c=con()
    if request.method=="POST":
        c.execute("INSERT INTO articles(article_no,name,pallet_type,cpp,storage_rule) VALUES(?,?,?,?,?) ON CONFLICT(article_no) DO UPDATE SET name=excluded.name,pallet_type=excluded.pallet_type,cpp=excluded.cpp,storage_rule=excluded.storage_rule",(request.form["no"].strip(),request.form["name"].strip(),request.form["ptype"],max(1,int(request.form["cpp"])),request.form["rule"])); c.commit(); c.close(); return redirect("/articles")
    rows=c.execute("SELECT * FROM articles ORDER BY article_no").fetchall(); c.close()
    b='''<div class="card"><h2>Artikelstamm</h2><form method="post"><div class="row"><div>Artikelnummer<input name="no" required></div><div>Artikelname<input name="name" required></div></div><div class="row"><div>Kartons pro Vollpalette<input type="number" min="1" name="cpp" required></div><div>Palettentyp<select name="ptype"><option>Euro</option><option>Einweg</option><option>Einweg 115 x 115</option></select></div></div>Lageregel<select name="rule"><option>Alle Ebenen</option><option>Nur Ebene 1</option><option>Nur Ebene 2-4</option></select><button>Speichern</button></form></div><div class="card"><h2>Artikel</h2><table><tr><th>Nr.</th><th>Name</th><th>Kartons/Palette</th><th>Palette</th><th>Regel</th></tr>'''
    for x in rows:b+=f'<tr><td>{x["article_no"]}</td><td>{x["name"]}</td><td>{x["cpp"]}</td><td>{x["pallet_type"]}</td><td>{x["storage_rule"]}</td></tr>'
    return page(b+'</table></div>')

@app.route("/containers",methods=["GET","POST"])
def containers():
    c=con()
    if request.method=="POST":
        g=int(request.form["gate"]) if request.form["gate"] else None
        c.execute("INSERT INTO containers(container_no,gate_no,status,created_at) VALUES(?,?,?,?)",(request.form["no"].strip(),g,request.form["status"],datetime.now().isoformat(timespec="minutes"))); c.commit(); c.close(); return redirect("/containers")
    rows=c.execute("SELECT * FROM containers ORDER BY id DESC").fetchall(); c.close()
    opts=''.join(f'<option>{g}</option>' for g in range(8,13))
    b=f'''<div class="card"><h2>Container anlegen</h2><form method="post">Containernummer<input name="no" required><div class="row"><div>Tor<select name="gate"><option value="">Kein Tor</option>{opts}</select></div><div>Status<select name="status"><option>geplant</option><option>vor Ort</option><option>verspÃ¤tet</option><option>bereit</option><option>erledigt</option></select></div></div><button>Anlegen</button></form></div><div class="card"><h2>Container</h2>'''
    b+=''.join(f'<p><a class="btn" href="/container/{x["id"]}">{x["container_no"]}</a> &nbsp; Tor {x["gate_no"] or "â"} Â· {x["status"]}</p>' for x in rows)
    return page(b+'</div>')

@app.route("/container/<int:cid>",methods=["GET","POST"])
def container(cid):
    c=con(); co=c.execute("SELECT * FROM containers WHERE id=?",(cid,)).fetchone()
    if request.method=="POST":
        a=c.execute("SELECT * FROM articles WHERE article_no=?",(request.form["article"],)).fetchone()
        if a:c.execute("INSERT INTO items(container_id,article_no,name,cartons,cpp,pallet_type) VALUES(?,?,?,?,?,?)",(cid,a["article_no"],a["name"],int(request.form["cartons"]),a["cpp"],a["pallet_type"]));c.commit()
        c.close();return redirect(f"/container/{cid}")
    arts=c.execute("SELECT * FROM articles ORDER BY article_no").fetchall(); its=c.execute("SELECT * FROM items WHERE container_id=?",(cid,)).fetchall();c.close()
    b=f'<div class="card"><h2>{co["container_no"]}</h2><p>Tor {co["gate_no"] or "â"} Â· <span class="badge">{co["status"]}</span></p></div><div class="card"><h2>Kartons hinzufÃ¼gen</h2>'
    if arts:b+='<form method="post">Artikel<select name="article">'+''.join(f'<option value="{a["article_no"]}">{a["article_no"]} â {a["name"]} ({a["cpp"]}/Palette)</option>' for a in arts)+'</select>Kartonanzahl<input type="number" min="1" name="cartons" required><button>HinzufÃ¼gen</button></form>'
    else:b+='<p>Bitte zuerst einen Artikel anlegen.</p>'
    b+='</div><div class="card"><h2>Containerinhalt</h2><table><tr><th>Artikel</th><th>Kartons</th><th>Voll</th><th>Rest</th><th>PlÃ¤tze</th></tr>'; total=0
    for x in its:
        f,r,p=calc(x["cartons"],x["cpp"]);total+=p;b+=f'<tr><td>{x["article_no"]}<br><span class="muted">{x["name"]}</span></td><td>{x["cartons"]}</td><td>{f}</td><td>{r}</td><td><b>{p}</b></td></tr>'
    return page(b+f'</table><h3>BenÃ¶tigte StellplÃ¤tze: {total}</h3></div>')

@app.route("/gates")
def gates():
    c=con();rows=c.execute("SELECT * FROM containers WHERE status!='erledigt' AND gate_no BETWEEN 8 AND 12").fetchall();c.close();d={x["gate_no"]:x for x in rows};b='<div class="card"><h2>Hallentore 8â12</h2><div class="gates">'
    for g in range(8,13):
        x=d.get(g);b+=f'<div class="gate"><div class="kpi">{g}</div>'+(f'<b>{x["container_no"]}</b><br>{x["status"]}' if x else '<span class="muted">Frei</span>')+'</div>'
    return page(b+'</div></div>')

init()
if __name__=="__main__":app.run(host="0.0.0.0",port=int(os.environ.get("PORT","8080")))