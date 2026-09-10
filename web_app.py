from flask import Flask, request, redirect
import sqlite3
import os
import math
from datetime import datetime

app = Flask(__name__)

DB = os.environ.get(
    "LAGERPRO_DB",
    os.path.join(os.path.dirname(__file__), "lagerpro.db")
)


# --------------------------------------------------
# DATENBANK
# --------------------------------------------------

def con():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def calc(cartons, cpp):
    cartons = int(cartons)
    cpp = max(1, int(cpp))

    full = cartons // cpp
    rest = cartons % cpp
    places = math.ceil(cartons / cpp) if cartons else 0

    return full, rest, places


def init_db():
    c = con()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS articles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        pallet_type TEXT NOT NULL,
        cpp INTEGER NOT NULL,
        storage_rule TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS containers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_no TEXT NOT NULL,
        gate_no INTEGER,
        status TEXT NOT NULL,
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
    """)

    c.commit()
    c.close()


# --------------------------------------------------
# DESIGN
# --------------------------------------------------

STYLE = """
<style>

:root {
    --bg: #07111f;
    --panel: #0d1b2d;
    --panel2: #11233a;
    --border: #203a5b;

    --text: #f6f8fc;
    --muted: #9cafc8;

    --yellow: #ffcc00;
    --green: #38df78;
    --red: #ff4d4d;
    --blue: #8eadd7;
}

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    min-height: 100%;
    background:
        radial-gradient(circle at top right, #102847 0, transparent 35%),
        linear-gradient(180deg, #07111f, #071523 60%, #06101c);

    color: var(--text);

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

body {
    padding-bottom: 95px;
}


/* HEADER */

.topbar {
    position: sticky;
    top: 0;
    z-index: 100;

    background: rgba(6, 17, 29, 0.96);
    border-bottom: 1px solid #19304d;

    backdrop-filter: blur(18px);
}

.top-inner {
    max-width: 1200px;
    margin: auto;

    padding: 12px 16px;

    display: flex;
    align-items: center;
    justify-content: space-between;
}

.logo img {
    width: auto;
    height: 67px;
    display: block;
}

.profile {
    display: flex;
    gap: 10px;
    align-items: center;
}

.avatar {
    height: 45px;
    width: 45px;

    border-radius: 50%;

    background: #233a5c;
    border: 1px solid #5877a5;

    display: grid;
    place-items: center;

    font-weight: 800;
}

.datetime {
    font-size: 12px;
    text-align: right;
    color: var(--muted);
}


/* MAIN */

.main {
    max-width: 1200px;
    margin: auto;
    padding: 14px;
}


/* HERO */

.hero {
    position: relative;
    overflow: hidden;

    min-height: 190px;

    border-radius: 18px;
    border: 1px solid var(--border);

    display: flex;
    align-items: center;

    padding: 24px;

    background:
        linear-gradient(
            90deg,
            rgba(5, 15, 28, .97),
            rgba(11, 33, 57, .92),
            rgba(11, 33, 57, .65)
        );
}

.hero::after {
    content: "";

    position: absolute;

    right: -100px;
    top: -80px;

    height: 360px;
    width: 420px;

    background:
        repeating-linear-gradient(
            90deg,
            rgba(255, 204, 0, .08) 0 35px,
            transparent 35px 70px
        );

    border-left: 6px solid var(--yellow);

    transform: skewX(-17deg);
}

.hero-content {
    position: relative;
    z-index: 2;
}

.hero-small {
    letter-spacing: 4px;
    color: #b7c8e0;
    font-size: 14px;
}

.hero h1 {
    margin: 5px 0 10px;
    font-size: 44px;
    line-height: 1;
}

.hero p {
    margin: 0;
    color: #b7c7dc;
    font-size: 17px;
}


/* CARDS */

.cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);

    gap: 12px;

    margin-top: 12px;
}

.card {
    border: 1px solid var(--border);
    border-radius: 18px;

    padding: 17px;

    background:
        linear-gradient(
            145deg,
            var(--panel),
            var(--panel2)
        );

    box-shadow:
        0 20px 45px rgba(0, 0, 0, .18);
}

.card-title {
    color: #b7c7dc;
    font-weight: 700;
    font-size: 14px;
}

.number {
    font-size: 38px;
    font-weight: 850;

    margin: 5px 0;
}

.muted {
    color: var(--muted);
}


/* PROGRESS */

.progress {
    height: 10px;

    border-radius: 30px;

    background: #263d5b;

    overflow: hidden;

    margin-top: 11px;
}

.progress span {
    display: block;
    height: 100%;

    background: var(--green);

    border-radius: 30px;
}


/* SECTIONS */

.section {
    margin-top: 13px;
}

.section-head {
    display: flex;
    align-items: center;
    justify-content: space-between;

    margin-bottom: 13px;
}

.section-head h2 {
    margin: 0;
    font-size: 20px;
}

.yellow-link {
    color: var(--yellow);
    text-decoration: none;
    font-weight: 800;
}


/* TORE */

.gates {
    display: grid;

    grid-template-columns:
        repeat(5, 1fr);

    gap: 9px;
}

.gate {
    background: #091728;

    border: 1px solid #223c5d;
    border-radius: 15px;

    padding: 15px;

    text-align: center;
}

.gate-number {
    font-weight: 800;
}

.dot {
    width: 21px;
    height: 21px;

    display: inline-block;

    border-radius: 50%;

    margin: 9px 0;
}

.green {
    background: var(--green);
}

.red {
    background: var(--red);
}

.yellow-dot {
    background: var(--yellow);
}

.gray {
    background: #60799e;
}

.status-green {
    color: var(--green);
    font-weight: 800;
}

.status-red {
    color: var(--red);
    font-weight: 800;
}

.status-yellow {
    color: var(--yellow);
    font-weight: 800;
}


/* 2 COLUMN */

.two {
    display: grid;
    grid-template-columns: 1fr 1fr;

    gap: 12px;
}


/* DONUT */

.donut-wrap {
    display: flex;

    align-items: center;
    gap: 20px;

    flex-wrap: wrap;
}

.donut {
    width: 155px;
    height: 155px;

    border-radius: 50%;

    display: grid;
    place-items: center;
}

.donut-inner {
    width: 95px;
    height: 95px;

    border-radius: 50%;

    background: #091726;

    display: grid;
    place-items: center;

    text-align: center;
}

.donut-number {
    font-size: 27px;
    font-weight: 900;
}


/* FORMS */

input,
select {
    width: 100%;

    padding: 12px;

    margin: 6px 0 12px;

    border-radius: 11px;

    border: 1px solid #294766;

    background: #071423;

    color: white;
}

button,
.button {
    display: inline-block;

    padding: 11px 15px;

    border: 0;
    border-radius: 11px;

    background: var(--yellow);

    color: #06111e;

    text-decoration: none;

    font-weight: 900;
}

.row {
    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 12px;
}


/* TABLE */

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    padding: 11px 8px;

    text-align: left;

    border-bottom:
        1px solid #203650;
}

th {
    color: #aebed3;
}

.badge {
    display: inline-block;

    padding: 5px 9px;

    border-radius: 20px;

    background: #213652;
}


/* PAGE HEADINGS */

.kicker {
    color: var(--yellow);

    font-size: 12px;

    letter-spacing: 2px;

    font-weight: 900;
}

.page-title {
    margin: 7px 0 15px;

    font-size: 30px;
}


/* MOBILE NAVIGATION */

.bottom-nav {
    position: fixed;

    left: 0;
    right: 0;
    bottom: 0;

    z-index: 200;

    background:
        rgba(6, 17, 29, .98);

    border-top:
        1px solid #1d3655;

    display: flex;

    justify-content: space-around;

    padding:
        7px 3px 11px;
}

.bottom-nav a {
    min-width: 65px;

    padding: 5px 2px;

    color: #9eb2cf;

    text-align: center;

    text-decoration: none;

    font-size: 12px;
}

.bottom-nav .icon {
    display: block;

    font-size: 22px;

    margin-bottom: 3px;
}

.bottom-nav a.active {
    color: var(--yellow);

    border-bottom:
        3px solid var(--yellow);
}


/* MOBILE */

@media (max-width: 760px) {

    .logo img {
        height: 55px;
    }

    .datetime {
        display: none;
    }

    .main {
        padding: 11px;
    }

    .hero {
        min-height: 170px;
        padding: 19px;
    }

    .hero h1 {
        font-size: 36px;
    }

    .hero p {
        font-size: 15px;
    }

    .cards {
        grid-template-columns:
            1fr 1fr;

        gap: 9px;
    }

    .number {
        font-size: 31px;
    }

    .card {
        padding: 14px;
    }

    .gates {
        grid-template-columns:
            repeat(5, 145px);

        overflow-x: auto;

        padding-bottom: 5px;
    }

    .two {
        grid-template-columns:
            1fr;
    }

    .row {
        grid-template-columns:
            1fr;
    }

    table {
        display: block;
        overflow-x: auto;
    }

}

</style>
"""


# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------

def bottom_nav(active):

    pages = [
        ("/", "⌂", "Dashboard", "dashboard"),
        ("/articles", "◈", "Artikel", "articles"),
        ("/containers", "▣", "Container", "containers"),
        ("/gates", "▥", "Tore", "gates"),
    ]

    result = '<div class="bottom-nav">'

    for url, icon, text, key in pages:

        css = "active" if active == key else ""

        result += f"""
        <a href="{url}" class="{css}">
            <span class="icon">{icon}</span>
            {text}
        </a>
        """

    result += "</div>"

    return result


def page(content, active="dashboard"):

    now = datetime.now()

    return f"""
    <html>

    <head>

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1"
        >

        <title>
            Lagerprozess
        </title>

        {STYLE}

    </head>

    <body>

        <header class="topbar">

            <div class="top-inner">

                <div class="logo">

                    <img
                        src="/static/drive_medical.png"
                        alt="Drive Medical"
                    >

                </div>

                <div class="profile">

                    <div class="avatar">
                        MB
                    </div>

                    <div class="datetime">

                        {now.strftime("%d.%m.%Y")}

                        <br>

                        {now.strftime("%H:%M")} Uhr

                    </div>

                </div>

            </div>

        </header>


        <main class="main">

            {content}

        </main>


        {bottom_nav(active)}

    </body>

    </html>
    """


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/")
def dashboard():

    c = con()

    article_count = c.execute(
        "SELECT COUNT(*) AS n FROM articles"
    ).fetchone()["n"]

    containers = c.execute("""
        SELECT *
        FROM containers
        WHERE status != 'erledigt'
        ORDER BY id DESC
    """).fetchall()

    items = c.execute(
        "SELECT * FROM items"
    ).fetchall()

    c.close()


    total_places = 332

    occupied = sum(
        calc(
            item["cartons"],
            item["cpp"]
        )[2]

        for item in items
    )

    occupied = min(
        occupied,
        total_places
    )

    free = (
        total_places
        - occupied
    )

    percent = (
        round(
            occupied
            / total_places
            * 100
        )
        if total_places
        else 0
    )


    gates = {
        g: None
        for g in range(8, 13)
    }


    for container in containers:

        gate = container["gate_no"]

        if (
            gate in gates
            and gates[gate] is None
        ):

            gates[gate] = container


    html = f"""

    <section class="hero">

        <div class="hero-content">

            <div class="hero-small">

                WILLKOMMEN BEI

            </div>

            <h1>
                Lagerprozess
            </h1>

            <p>

                Übersicht · Kontrolle ·
                Effiziente Lagerhaltung

            </p>

        </div>

    </section>



    <section class="cards">


        <div class="card">

            <div class="card-title">
                Gesamtstellplätze
            </div>

            <div class="number">
                332
            </div>

            <div class="muted">

                4 Ebenen ×
                83 Stellplätze

            </div>

        </div>


        <div class="card">

            <div class="card-title">

                Belegte Stellplätze

            </div>

            <div class="number">

                {occupied}

            </div>

            <div class="muted">

                {percent} % Auslastung

            </div>

            <div class="progress">

                <span
                    style="
                    width:{percent}%
                    "
                ></span>

            </div>

        </div>


        <div class="card">

            <div class="card-title">

                Freie Stellplätze

            </div>

            <div class="number">

                {free}

            </div>

            <div class="muted">

                {100 - percent}
                % verfügbar

            </div>

        </div>


        <div class="card">

            <div class="card-title">

                Aktive Container

            </div>

            <div class="number">

                {len(containers)}

            </div>

            <div class="muted">

                Tore 8–12

            </div>

        </div>


    </section>



    <section class="card section">

        <div class="section-head">

            <h2>

                Tore 8–12

            </h2>

            <a
                href="/gates"
                class="yellow-link"
            >

                Alle anzeigen →

            </a>

        </div>


        <div class="gates">

    """


    for gate in range(8, 13):

        item = gates[gate]


        if not item:

            html += f"""

            <div class="gate">

                <div class="gate-number">

                    Tor {gate}

                </div>

                <span
                    class="
                    dot gray
                    "
                ></span>

                <br>

                <span class="muted">

                    Frei

                </span>

            </div>

            """

            continue


        status = (
            item["status"]
            or ""
        ).lower()


        if "versp" in status:

            dot = "red"
            status_class = "status-red"

        elif (
            "bereit" in status
            or "vor ort" in status
        ):

            dot = "green"
            status_class = "status-green"

        else:

            dot = "yellow-dot"
            status_class = "status-yellow"


        html += f"""

        <div class="gate">

            <div class="gate-number">

                Tor {gate}

            </div>

            <span
                class="
                dot {dot}
                "
            ></span>

            <br>

            <b>

                {item["container_no"]}

            </b>

            <br>

            <span
                class="
                {status_class}
                "
            >

                {item["status"]}

            </span>

        </div>

        """


    html += f"""

        </div>

    </section>



    <section class="two">


        <div class="card section">

            <div class="section-head">

                <h2>
                    Lagerauslastung
                </h2>

            </div>


            <div class="donut-wrap">


                <div

                    class="donut"

                    style="
                    background:
                    conic-gradient(
                        var(--green)
                        0 {percent}%,
                        #7896bd
                        {percent}% 100%
                    )
                    "
                >

                    <div
                        class="
                        donut-inner
                        "
                    >

                        <div>

                            <div
                                class="
                                donut-number
                                "
                            >

                                {percent} %

                            </div>

                            <div
                                class="
                                muted
                                "
                            >

                                Auslastung

                            </div>

                        </div>

                    </div>

                </div>


                <div>

                    <p>

                        🟢 Belegt

                        <b>
                            {occupied}
                        </b>

                    </p>

                    <p>

                        🔵 Frei

                        <b>
                            {free}
                        </b>

                    </p>

                    <p
                        class="
                        muted
                        "
                    >

                        Von 332
                        Stellplätzen

                    </p>

                </div>


            </div>

        </div>



        <div class="card section">

            <div class="section-head">

                <h2>

                    Aktuelle Container

                </h2>

                <a
                    href="/containers"
                    class="yellow-link"
                >

                    Alle anzeigen →

                </a>

            </div>


            <table>

                <tr>

                    <th>
                        Container
                    </th>

                    <th>
                        Status
                    </th>

                    <th>
                        Tor
                    </th>

                </tr>

    """


    for container in containers[:6]:

        html += f"""

        <tr>

            <td>

                <a
                    href="
                    /container/{container["id"]}
                    "

                    style="
                    color:white
                    "
                >

                    {container["container_no"]}

                </a>

            </td>

            <td>

                {container["status"]}

            </td>

            <td>

                {
                    container["gate_no"]
                    or "–"
                }

            </td>

        </tr>

        """


    if not containers:

        html += """

        <tr>

            <td
                colspan="3"
                class="muted"
            >

                Noch keine Container.

            </td>

        </tr>

        """


    html += """

            </table>

        </div>


    </section>

    """


    return page(
        html,
        "dashboard"
    )


# --------------------------------------------------
# ARTIKEL
# --------------------------------------------------

@app.route(
    "/articles",
    methods=["GET", "POST"]
)
def articles():

    c = con()


    if request.method == "POST":

        c.execute("""
        INSERT INTO articles(
            article_no,
            name,
            pallet_type,
            cpp,
            storage_rule
        )
        VALUES(?,?,?,?,?)

        ON CONFLICT(article_no)

        DO UPDATE SET

            name=excluded.name,
            pallet_type=excluded.pallet_type,
            cpp=excluded.cpp,
            storage_rule=excluded.storage_rule
        """,

        (
            request.form["no"].strip(),

            request.form["name"].strip(),

            request.form["ptype"],

            max(
                1,
                int(
                    request.form["cpp"]
                )
            ),

            request.form["rule"]
        ))


        c.commit()

        c.close()

        return redirect(
            "/articles"
        )


    rows = c.execute("""
        SELECT *
        FROM articles
        ORDER BY article_no
    """).fetchall()

    c.close()


    html = """

    <div class="kicker">
        ARTIKELSTAMM
    </div>

    <h1 class="page-title">
        Artikel verwalten
    </h1>


    <div class="card">

        <form method="post">


            <div class="row">

                <div>

                    Artikelnummer

                    <input
                        name="no"
                        required
                    >

                </div>


                <div>

                    Artikelname

                    <input
                        name="name"
                        required
                    >

                </div>

            </div>


            <div class="row">


                <div>

                    Kartons pro Vollpalette

                    <input
                        type="number"
                        min="1"
                        name="cpp"
                        required
                    >

                </div>


                <div>

                    Palettentyp

                    <select
                        name="ptype"
                    >

                        <option>
                            Euro
                        </option>

                        <option>
                            Einweg
                        </option>

                        <option>
                            Einweg 115 x 115
                        </option>

                    </select>

                </div>

            </div>


            Lageregel

            <select
                name="rule"
            >

                <option>
                    Alle Ebenen
                </option>

                <option>
                    Nur Ebene 1
                </option>

                <option>
                    Nur Ebene 2-4
                </option>

            </select>


            <button>

                Artikel speichern

            </button>


        </form>

    </div>


    <div class="card">

        <table>

            <tr>

                <th>Nr.</th>

                <th>Name</th>

                <th>
                    Kartons/Palette
                </th>

                <th>
                    Palette
                </th>

                <th>
                    Regel
                </th>

            </tr>

    """


    for item in rows:

        html += f"""

        <tr>

            <td>
                {item["article_no"]}
            </td>

            <td>
                {item["name"]}
            </td>

            <td>
                {item["cpp"]}
            </td>

            <td>
                {item["pallet_type"]}
            </td>

            <td>
                {item["storage_rule"]}
            </td>

        </tr>

        """


    html += """

        </table>

    </div>

    """


    return page(
        html,
        "articles"
    )


# --------------------------------------------------
# CONTAINER
# --------------------------------------------------

@app.route(
    "/containers",
    methods=["GET", "POST"]
)
def containers():

    c = con()


    if request.method == "POST":

        gate = (

            int(
                request.form["gate"]
            )

            if request.form["gate"]

            else None
        )


        c.execute("""
        INSERT INTO containers(
            container_no,
            gate_no,
            status,
            created_at
        )

        VALUES(?,?,?,?)
        """,

        (
            request.form["no"].strip(),

            gate,

            request.form["status"],

            datetime.now().isoformat(
                timespec="minutes"
            )
        ))


        c.commit()

        c.close()

        return redirect(
            "/containers"
        )


    rows = c.execute("""
        SELECT *
        FROM containers
        ORDER BY id DESC
    """).fetchall()

    c.close()


    gates = "".join(

        f"<option>{x}</option>"

        for x in range(8, 13)
    )


    html = f"""

    <div class="kicker">
        CONTAINER
    </div>

    <h1 class="page-title">
        Containerverwaltung
    </h1>


    <div class="card">

        <form method="post">


            Containernummer

            <input
                name="no"
                required
            >


            <div class="row">


                <div>

                    Tor

                    <select
                        name="gate"
                    >

                        <option value="">
                            Kein Tor
                        </option>

                        {gates}

                    </select>

                </div>


                <div>

                    Status

                    <select
                        name="status"
                    >

                        <option>
                            geplant
                        </option>

                        <option>
                            vor Ort
                        </option>

                        <option>
                            verspätet
                        </option>

                        <option>
                            bereit
                        </option>

                        <option>
                            erledigt
                        </option>

                    </select>

                </div>


            </div>


            <button>

                Container anlegen

            </button>


        </form>

    </div>


    <div class="card">

        <table>

            <tr>

                <th>
                    Container
                </th>

                <th>
                    Tor
                </th>

                <th>
                    Status
                </th>

            </tr>

    """


    for container in rows:

        html += f"""

        <tr>

            <td>

                <a
                    href="
                    /container/{container["id"]}
                    "

                    style="
                    color:white
                    "
                >

                    {container["container_no"]}

                </a>

            </td>


            <td>

                {
                    container["gate_no"]
                    or "–"
                }

            </td>


            <td>

                <span
                    class="badge"
                >

                    {container["status"]}

                </span>

            </td>

        </tr>

        """


    html += """

        </table>

    </div>

    """


    return page(
        html,
        "containers"
    )


# --------------------------------------------------
# CONTAINER DETAILS
# --------------------------------------------------

@app.route(
    "/container/<int:cid>",
    methods=["GET", "POST"]
)
def container_detail(cid):

    c = con()


    container = c.execute(
        """
        SELECT *
        FROM containers
        WHERE id=?
        """,

        (cid,)
    ).fetchone()


    if not container:

        c.close()

        return redirect(
            "/containers"
        )


    if request.method == "POST":

        article = c.execute(
            """
            SELECT *
            FROM articles
            WHERE article_no=?
            """,

            (
                request.form[
                    "article"
                ],
            )
        ).fetchone()


        if article:

            c.execute("""
            INSERT INTO items(
                container_id,
                article_no,
                name,
                cartons,
                cpp,
                pallet_type
            )

            VALUES(?,?,?,?,?,?)
            """,

            (
                cid,

                article["article_no"],

                article["name"],

                int(
                    request.form[
                        "cartons"
                    ]
                ),

                article["cpp"],

                article["pallet_type"]
            ))


            c.commit()


        c.close()

        return redirect(
            f"/container/{cid}"
        )


    articles = c.execute("""
        SELECT *
        FROM articles
        ORDER BY article_no
    """).fetchall()


    items = c.execute("""
        SELECT *
        FROM items
        WHERE container_id=?
    """,

    (cid,)
    ).fetchall()


    c.close()


    html = f"""

    <div class="kicker">

        CONTAINERDETAIL

    </div>


    <h1 class="page-title">

        {container["container_no"]}

    </h1>


    <div class="card">

        <b>

            Tor {
                container["gate_no"]
                or "–"
            }

        </b>

        &nbsp;

        <span class="badge">

            {container["status"]}

        </span>

    </div>



    <div class="card">

        <h2>

            Kartons hinzufügen

        </h2>

    """


    if articles:

        html += """

        <form method="post">

            Artikel

            <select name="article">

        """


        for article in articles:

            html += f"""

            <option
                value="
                {article["article_no"]}
                "
            >

                {article["article_no"]}
                –
                {article["name"]}

                (
                {article["cpp"]}
                /Palette
                )

            </option>

            """


        html += """

            </select>


            Kartonanzahl

            <input
                type="number"
                min="1"
                name="cartons"
                required
            >


            <button>

                Hinzufügen

            </button>


        </form>

        """


    else:

        html += """

        <p class="muted">

            Bitte zuerst
            einen Artikel anlegen.

        </p>

        """


    html += """

    </div>


    <div class="card">

        <h2>

            Containerinhalt

        </h2>


        <table>

            <tr>

                <th>
                    Artikel
                </th>

                <th>
                    Kartons
                </th>

                <th>
                    Voll
                </th>

                <th>
                    Rest
                </th>

                <th>
                    Plätze
                </th>

            </tr>

    """


    total = 0


    for item in items:

        full, rest, places = calc(

            item["cartons"],

            item["cpp"]
        )


        total += places


        html += f"""

        <tr>

            <td>

                {item["article_no"]}

                <br>

                <span class="muted">

                    {item["name"]}

                </span>

            </td>


            <td>

                {item["cartons"]}

            </td>


            <td>

                {full}

            </td>


            <td>

                {rest}

            </td>


            <td>

                <b>

                    {places}

                </b>

            </td>

        </tr>

        """


    html += f"""

        </table>


        <h3>

            Benötigte Stellplätze:

            {total}

        </h3>


    </div>

    """


    return page(
        html,
        "containers"
    )


# --------------------------------------------------
# TORE
# --------------------------------------------------

@app.route("/gates")
def gates():

    c = con()


    rows = c.execute("""
        SELECT *
        FROM containers

        WHERE
            status != 'erledigt'

        AND gate_no
            BETWEEN 8 AND 12
    """).fetchall()


    c.close()


    gate_data = {

        item["gate_no"]: item

        for item in rows
    }


    html = """

    <div class="kicker">

        TORE

    </div>


    <h1 class="page-title">

        Hallentore 8–12

    </h1>


    <div class="card">

        <div class="gates">

    """


    for gate in range(8, 13):

        item = gate_data.get(
            gate
        )


        if item:

            html += f"""

            <div class="gate">

                <div class="gate-number">

                    Tor {gate}

                </div>

                <span
                    class="
                    dot green
                    "
                ></span>

                <br>

                <b>

                    {item["container_no"]}

                </b>

                <br>

                {item["status"]}

            </div>

            """


        else:

            html += f"""

            <div class="gate">

                <div class="gate-number">

                    Tor {gate}

                </div>

                <span
                    class="
                    dot gray
                    "
                ></span>

                <br>

                <span class="muted">

                    Frei

                </span>

            </div>

            """


    html += """

        </div>

    </div>

    """


    return page(
        html,
        "gates"
    )


# --------------------------------------------------
# START
# --------------------------------------------------

init_db()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                "8080"
            )
        )
    )