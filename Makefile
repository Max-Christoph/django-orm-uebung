# Makefile -- Kurzbefehle fuer die Datenbank der ORM-Uebung.
#
# Alle Ziele sind "phony": sie erzeugen keine Datei dieses Namens.

.PHONY: help up down reset psql logs fixture status

help:
	@echo "make up       Datenbank und Adminer starten"
	@echo "make down     Container stoppen (Daten bleiben erhalten)"
	@echo "make reset    Container stoppen UND Daten loeschen (Volume entfernen)"
	@echo "make status   Zustand der Container anzeigen"
	@echo "make psql     psql-Shell in der Datenbank oeffnen"
	@echo "make logs     Logs der Datenbank anzeigen"
	@echo "make fixture  fixtures/demo.json neu erzeugen"

up:
	docker compose up -d
	@echo "Adminer: http://localhost:8080  (System: PostgreSQL, Server: db, Benutzer/Passwort/DB: siehe .env)"

down:
	docker compose down

reset:
	docker compose down -v
	@echo "Datenbank-Volume entfernt. Naechstes 'make up' startet mit leerer Datenbank."

status:
	docker compose ps

psql:
	docker compose exec db psql -U $${POSTGRES_USER:-bibliothek} -d $${POSTGRES_DB:-bibliothek}

logs:
	docker compose logs -f db

fixture:
	python scripts/make_fixture.py
