# Änderungsprotokoll

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
