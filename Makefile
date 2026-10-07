# Makefile -- Kurzbefehle fuer die ORM-Uebung.
#
# Django laeuft im Container "web". Diese Ziele ersparen dir das lange
# "docker compose exec ..." -- brauchen aber kein lokales Python.

.PHONY: help up down reset psql logs shell dbshell makemigrations migrate seed fixture status run adminer

help:
	@echo "make up             Datenbank, Schema und Testdaten starten (docker compose up -d)"
	@echo "make shell          Django-Shell im Container (hier arbeitest du)"
	@echo "make run F=x.py     eigenes Skript im Container ausfuehren"
	@echo "make makemigrations Migration aus deinen Modellen erzeugen"
	@echo "make migrate        Migrationen einspielen"
	@echo "make seed           Testdaten laden, falls die Tabellen leer sind"
	@echo "make dbshell        psql im web-Container"
	@echo "make psql           psql im db-Container"
	@echo "make logs           Logs aller Dienste, mitlaufend"
	@echo "make status         Zustand der Container"
	@echo "make down           Container stoppen (Daten bleiben)"
	@echo "make reset          Container stoppen UND Daten loeschen"
	@echo "make fixture        fixtures/demo.json neu erzeugen (braucht lokales Python)"

up:
	docker compose up -d
	@echo
	@echo "Kontrolle:  docker compose exec web python manage.py shell"
	@echo "Adminer:    make adminer   (eigenes Profil, weil Port 8080 oft belegt ist)"

# Adminer startet nicht bei "make up", weil Port 8080 auf vielen Rechnern belegt ist.
# Ohne eigenes Profil wuerde der Portfehler "web" mitreissen.
adminer:
	docker compose --profile adminer up -d adminer
	@echo "Adminer: http://localhost:$${ADMINER_PORT:-8080}   (System PostgreSQL, Server db, bibliothek/bibliothek)"

down:
	docker compose down

reset:
	docker compose down -v
	@echo "Datenbank-Volume entfernt. Naechstes 'make up' richtet alles neu ein."

status:
	docker compose ps

# --- Hier arbeitest du ------------------------------------------------------
shell:
	docker compose exec web python manage.py shell

# Eigenes Skript im Container ausfuehren: make run F=mein_skript.py
# "-T" schaltet die Pseudo-TTY ab, damit die Ausgabe auch beim Weiterleiten
# oder in Skripten sauber ankommt.
run:
	docker compose exec -T web python manage.py shell -c "exec(open('$(F)').read())"

makemigrations:
	docker compose exec web python manage.py makemigrations

migrate:
	docker compose exec web python manage.py migrate

seed:
	docker compose exec web python manage.py seed

# --- Nachschauen ------------------------------------------------------------
dbshell:
	docker compose exec web python manage.py dbshell

psql:
	docker compose exec db psql -U $${POSTGRES_USER:-bibliothek} -d $${POSTGRES_DB:-bibliothek}

logs:
	docker compose logs -f

# --- Fixture neu erzeugen (optional, braucht lokales Python) ----------------
fixture:
	python scripts/make_fixture.py
