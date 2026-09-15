# LagerPro V39

Webbasierte Lagerverwaltung für Artikel, Ladungsträger, Lagerplätze, Container,
Wareneingang, Inventur, Qualität, Nachbestellung und E-Mail-Benachrichtigungen.

## V39-Neuerungen

- echte PostgreSQL-Unterstützung für Railway über `DATABASE_URL`
- SQLite bleibt für lokale Tests verfügbar
- CSRF-Schutz für alle schreibenden Formulare
- sichere Session-Cookies und HTTP-Sicherheitsheader
- atomare Container-Fertigmail mit Schutz gegen Doppelversand
- Wiederholung fehlgeschlagener Nachbestellmails
- getrennte Empfänger für Containerleitung und Einkauf
- installierbare iPhone-/Android-PWA mit Offline-Hinweis
- automatische SQLite- und PostgreSQL-Tests über GitHub Actions
- SMTP-Geheimnisse können sicher als Railway-Variablen hinterlegt werden
- PostgreSQL-Status im Healthcheck `/api/health`
- korrigierte Railway-Startkonfiguration

## Railway einrichten

1. Im bestehenden Railway-Projekt einen PostgreSQL-Dienst hinzufügen.
2. Den LagerPro-Dienst mit der PostgreSQL-Variable `DATABASE_URL` verbinden.
3. Eine lange zufällige Variable `LAGERPRO_SECRET` setzen.
4. SMTP-Variablen eintragen und anschließend in LagerPro eine Test-Mail senden.
5. Nach dem Deployment `/api/health` öffnen. Dort muss
   `"database_backend":"postgresql"` und `"version":"V39"` erscheinen.

## Benötigte Railway-Variablen

| Variable | Bedeutung |
| --- | --- |
| `DATABASE_URL` | Wird durch Railway PostgreSQL bereitgestellt |
| `LAGERPRO_SECRET` | Mindestens 32 zufällige Zeichen |
| `SMTP_HOST` | SMTP-Server, z. B. der Firmen-Mailserver |
| `SMTP_PORT` | Normalerweise 587 für STARTTLS |
| `SMTP_USER` | SMTP-Benutzername |
| `SMTP_PASSWORD` | Passwort oder App-Passwort, als Secret speichern |
| `SMTP_SENDER` | Absenderadresse |
| `SMTP_STARTTLS` | `1` für STARTTLS |
| `SMTP_SSL` | Nur bei direktem SSL auf `1` setzen |
| `NOTIFICATION_EMAILS` | Empfänger, mehrere mit Komma getrennt |
| `CONTAINER_NOTIFICATION_EMAILS` | Empfänger für fertige Container |
| `REORDER_NOTIFICATION_EMAILS` | Empfänger für Nachbestellungen |

## Erster Start

Beim ersten Aufruf wird der Administrator angelegt. Danach ist ohne Anmeldung
kein Zugriff auf Lagerdaten möglich. Das Standardlager wird automatisch erzeugt:

- Gänge 1–7: jeweils 89 Positionen pro Ebene
- übrige Gänge: jeweils 83 Positionen pro Ebene
- Ebenen 1–4
- Positionen 21–23 als 3er-Stellplätze

## Lokaler Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export LAGERPRO_SECURE_COOKIES=0
python web_app.py
```

Ohne `DATABASE_URL` verwendet LagerPro die lokale Datei `lagerpro.db`.

## Vorhandene SQLite-Daten übernehmen

Ein alter Datenbestand kann einmalig und ohne Löschen vorhandener PostgreSQL-
Daten übernommen werden:

```bash
SQLITE_SOURCE=/pfad/lagerpro.db DATABASE_URL=postgresql://... \
python migrate_sqlite_to_postgres.py
```

Vorher immer eine Kopie der SQLite-Datei anlegen. Danach Bestände, Container und
Bewegungsverlauf stichprobenartig vergleichen.

## Datensicherung

Bei PostgreSQL müssen Sicherungen im Railway-Datenbankdienst aktiviert werden.
Vor dem Firmenbetrieb sollten tägliche Backups und eine Wiederherstellungsprobe
eingerichtet werden. Die eingebaute Dateisicherung gilt nur für lokalen
SQLite-Betrieb.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

GitHub Actions prüft zusätzlich jeden Push gegen PostgreSQL 16.

## iPhone installieren

LagerPro in Safari öffnen, unten auf **Teilen** und anschließend auf
**Zum Home-Bildschirm** tippen. Buchungen werden aus Sicherheitsgründen nicht
offline gespeichert; bei fehlender Verbindung erscheint ein Offline-Hinweis.
