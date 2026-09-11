# LagerPro V37

Mobile Lagerverwaltungs-Web-App für Container, Artikelstamm, Ladungsträger,
Lagerplätze, Inventur, Nachbestellung und Auswertungen.

## Start

```bash
pip install -r requirements.txt
python web_app.py
```

Beim ersten Aufruf wird unter `/setup` das Administratorkonto angelegt.

## Railway

Der Dienst startet über den vorhandenen `Procfile` mit Gunicorn. Für einen
dauerhaften Produktivbetrieb müssen in Railway folgende Variablen gesetzt sein:

- `LAGERPRO_SECRET`: langer zufälliger Wert für die Sitzungsverschlüsselung
- `LAGERPRO_DB=/data/lagerpro.db`: Datenbankdatei auf einem Railway-Volume
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_SENDER`
- optional `SMTP_STARTTLS=1` oder `SMTP_SSL=1`
- optional `LAGERPRO_NOTIFICATION_EMAILS`, `LAGERPRO_CONTAINER_EMAILS`,
  `LAGERPRO_REORDER_EMAILS`

Das Railway-Volume muss unter `/data` eingehängt sein. Ohne Volume liegt SQLite
im kurzlebigen Container-Dateisystem und Daten können bei einem Deployment
verloren gehen.

## Lagerlayout

- 30 Gänge, vier Ebenen
- Gänge 1–7: 89 Positionen je Ebene
- Gänge 8–30: 83 Positionen je Ebene
- Positionen 21–23: Kapazität 3, alle übrigen Positionen: Kapazität 4
- Ebene 1 ist die Bodenebene
- Euro- und Einweg-Ladungsträger dürfen nicht direkt nebeneinander stehen
- jeder gebuchte Platz erhält einen eigenen Ladungsträger und Bewegungsverlauf

## Tests

```bash
python -m unittest -v
```
