from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
import os
import math

app = Flask(__name__)

DB = os.path.join(os.path.dirname(__file__), "lagerpro.db")


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            pallet_type TEXT NOT NULL,
            cartons_per_pallet INTEGER NOT NULL DEFAULT 1,
            storage_rule TEXT DEFAULT 'Alle Ebenen'
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS containers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            container_no TEXT NOT NULL,
            gate_no INTEGER,
            status TEXT DEFAULT 'offen',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS container_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            container_id INTEGER NOT NULL,
            article_no TEXT NOT NULL,
            name TEXT NOT NULL,
            cartons INTEGER NOT NULL,
            cartons_per_pallet INTEGER NOT NULL,
            pallet_type TEXT NOT NULL,
            FOREIGN KEY(container_id) REFERENCES containers(id)
        )
    """)

    con.commit()
    con.close()


init_db()


@app.route("/")
def dashboard():
    con = db()

    articles = con.execute(
        "SELECT * FROM articles ORDER BY article_no"
    ).fetchall()

    containers = con.execute("""
        SELECT * FROM containers
        ORDER BY id DESC
    """).fetchall()

    total_cartons = con.execute("""
        SELECT COALESCE(SUM(cartons), 0)
        FROM container_items
    """).fetchone()[0]

    pallet_places = 0

    rows = con.execute("""
        SELECT cartons, cartons_per_pallet
        FROM container_items
    """).fetchall()

    for row in rows:
        cpp = max(1, row["cartons_per_pallet"])
        pallet_places += math.ceil(row["cartons"] / cpp)

    con.close()

    return render_template_string(
        PAGE,
        articles=articles,
        containers=containers,
        total_cartons=total_cartons,
        pallet_places=pallet_places
    )


@app.route("/article/add", methods=["POST"])
def add_article():
    article_no = request.form["article_no"].strip()
    name = request.form["name"].strip()
    pallet_type = request.form["pallet_type"]
    cartons_per_pallet = max(
        1, int(request.form["cartons_per_pallet"])
    )
    storage_rule = request.form["storage_rule"]

    con = db()

    con.execute("""
        INSERT OR REPLACE INTO articles
        (article_no, name, pallet_type,
         cartons_per_pallet, storage_rule)
        VALUES (?, ?, ?, ?, ?)
    """, (
        article_no,
        name,
        pallet_type,
        cartons_per_pallet,
        storage_rule
    ))

    con.commit()
    con.close()

    return redirect(url_for("dashboard"))


@app.route("/container/add", methods=["POST"])
def add_container():
    container_no = request.form["container_no"].strip()
    gate = request.form.get("gate_no")

    gate = int(gate) if gate else None

    con = db()

    con.execute("""
        INSERT INTO containers
        (container_no, gate_no, status)
        VALUES (?, ?, 'offen')
    """, (container_no, gate))

    con.commit()
    con.close()

    return redirect(url_for("dashboard"))


@app.route("/container/<int:container_id>/delete", methods=["POST"])
def delete_container(container_id):
    con = db()

    con.execute(
        "DELETE FROM container_items WHERE container_id=?",
        (container_id,)
    )

    con.execute(
        "DELETE FROM containers WHERE id=?",
        (container_id,)
    )

    con.commit()
    con.close()

    return redirect(url_for("dashboard"))


PAGE = """
<!doctype html>
<html lang="de">
<head>

<meta charset="utf-8">
<meta name="viewport"
content="width=device-width,initial-scale=1,viewport-fit=cover">

<title>LagerPro</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #0b0f17;
    color: #f4f7fb;
    font-family: -apple-system, BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
}

header {
    padding: 22px;
    background: #111827;
    border-bottom: 1px solid #263244;
}

.logo {
    font-size: 26px;
    font-weight: 800;
}

.subtitle {
    color: #94a3b8;
    margin-top: 4px;
}

main {
    padding: 18px;
    max-width: 1200px;
    margin: auto;
}

.cards {
    display: grid;
    grid-template-columns: repeat(2,1fr);
    gap: 12px;
}

.card {
    background: #131b29;
    border: 1px solid #263244;
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 16px;
}

.number {
    font-size: 30px;
    font-weight: 800;
}

.label {
    color: #94a3b8;
}

h2 {
    margin-top: 4px;
}

input, select {
    width: 100%;
    padding: 13px;
    margin: 6px 0;
    background: #0d1420;
    border: 1px solid #334155;
    border-radius: 10px;
    color: white;
    font-size: 16px;
}

button {
    border: 0;
    border-radius: 10px;
    padding: 12px 15px;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
}

.primary {
    background: #6366f1;
    color: white;
    width: 100%;
    margin-top: 8px;
}

.delete {
    background: #7f1d1d;
    color: white;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 11px 8px;
    border-bottom: 1px solid #263244;
    text-align: left;
}

th {
    color: #94a3b8;
}

.scroll {
    overflow-x: auto;
}

@media(min-width:800px) {
    .cards {
        grid-template-columns: repeat(4,1fr);
    }

    .forms {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
    }
}

</style>

</head>

<body>

<header>
<div class="logo">📦 LagerPro</div>
<div class="subtitle">
Warehouse Management
</div>
</header>

<main>

<div class="cards">

<div class="card">
<div class="number">{{ articles|length }}</div>
<div class="label">Artikel</div>
</div>

<div class="card">
<div class="number">{{ containers|length }}</div>
<div class="label">Container</div>
</div>

<div class="card">
<div class="number">{{ total_cartons }}</div>
<div class="label">Kartons</div>
</div>

<div class="card">
<div class="number">{{ pallet_places }}</div>
<div class="label">Palettenplätze</div>
</div>

</div>


<div class="forms">

<div class="card">

<h2>Artikel hinzufügen</h2>

<form method="post" action="/article/add">

<input
name="article_no"
placeholder="Artikelnummer"
required>

<input
name="name"
placeholder="Artikelname"
required>

<select name="pallet_type">
<option>Euro</option>
<option>Einweg</option>
<option>115x115</option>
</select>

<input
name="cartons_per_pallet"
type="number"
min="1"
placeholder="Kartons pro Vollpalette"
required>

<select name="storage_rule">
<option>Alle Ebenen</option>
<option>Nur Ebene 1</option>
<option>Nur Ebenen 2-4</option>
</select>

<button class="primary">
Artikel speichern
</button>

</form>

</div>


<div class="card">

<h2>Container hinzufügen</h2>

<form method="post" action="/container/add">

<input
name="container_no"
placeholder="Containernummer"
required>

<select name="gate_no">

<option value="">
Kein Tor
</option>

<option value="8">Tor 8</option>
<option value="9">Tor 9</option>
<option value="10">Tor 10</option>
<option value="11">Tor 11</option>
<option value="12">Tor 12</option>

</select>

<button class="primary">
Container anlegen
</button>

</form>

</div>

</div>


<div class="card">

<h2>Container</h2>

<div class="scroll">

<table>

<tr>
<th>Container</th>
<th>Tor</th>
<th>Status</th>
<th></th>
</tr>

{% for c in containers %}

<tr>

<td>{{ c.container_no }}</td>

<td>
{% if c.gate_no %}
Tor {{ c.gate_no }}
{% else %}
-
{% endif %}
</td>

<td>{{ c.status }}</td>

<td>

<form
method="post"
action="/container/{{ c.id }}/delete"
onsubmit="return confirm('Container wirklich löschen?');">

<button class="delete">
Löschen
</button>

</form>

</td>

</tr>

{% endfor %}

</table>

</div>

</div>


<div class="card">

<h2>Artikelstamm</h2>

<div class="scroll">

<table>

<tr>
<th>Nr.</th>
<th>Artikel</th>
<th>Palette</th>
<th>Kartons/Palette</th>
<th>Lagerregel</th>
</tr>

{% for a in articles %}

<tr>

<td>{{ a.article_no }}</td>
<td>{{ a.name }}</td>
<td>{{ a.pallet_type }}</td>
<td>{{ a.cartons_per_pallet }}</td>
<td>{{ a.storage_rule }}</td>

</tr>

{% endfor %}

</table>

</div>

</div>

</main>

</body>
</html>
"""


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)