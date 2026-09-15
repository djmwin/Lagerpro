# Änderungsprotokoll

## V39

- echte SQLite-/PostgreSQL-Datenbankschicht und Schema-Version
- CSRF, sichere Cookies, Proxy-HTTPS und HTTP-Sicherheitsheader
- Rollenprüfung für Leitungs- und Adminbereiche
- atomarer Schutz gegen doppelte Container-Fertigmails
- vollständige Bewegungsdaten und Euro-/Einweg-Prüfung bei Direktbuchungen
- getrennte E-Mail-Empfänger und Wiederholung fehlgeschlagener Nachbestellmails
- SMTP-Passwörter ausschließlich aus geschützten Umgebungsvariablen
- installierbare PWA mit App-Symbol und Offline-Hinweis
- CI-Tests für SQLite und PostgreSQL
- nicht-destruktives Werkzeug zur Übernahme bestehender SQLite-Daten

## V38

- Railway-PostgreSQL über `DATABASE_URL`
- lokaler SQLite-Fallback
- PostgreSQL-kompatible Schemaerstellung und Abfragen
- CSRF-Schutz für sämtliche POST-Formulare
- sicherere Session-Cookies und HTTP-Header
- Proxy-Unterstützung für Railway-HTTPS
- atomarer Schutz gegen doppelte Container-Fertigmails
- SMTP-Secrets über Railway-Umgebungsvariablen
- PostgreSQL-Hinweis bei Datensicherungen
- Healthcheck meldet Version und Datenbanktyp
- Gunicorn-Produktionsstart
- automatisierte Kern- und Seitentests
