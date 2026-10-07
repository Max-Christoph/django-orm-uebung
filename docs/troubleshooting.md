# Troubleshooting

Fünf Probleme, die in der Übung praktisch immer auftreten — plus die Standardlösung.

---

## 1. „Port 5433 is already allocated" / Port belegt

**Meldung:**

```
Error response from daemon: driver failed programming external connectivity ...:
Bind for 0.0.0.0:5433 failed: port is already allocated
```

**Ursache:** Auf 5433 läuft schon etwas — meist ein älterer Container dieser Übung oder eine
zweite PostgreSQL-Instanz.

**Prüfen, wer den Port hält:**

```bash
# Linux / macOS
sudo lsof -i :5433
# oder
sudo ss -tlnp | grep 5433

# Windows (PowerShell)
netstat -ano | findstr :5433
```

**Lösen:** Den belegenden Prozess beenden. Ist es ein alter Container dieser Übung:

```bash
docker compose down
docker ps -a          # nach bibliothek-db suchen
```

Bleibt der Port belegt, in `.env` einen anderen Wert setzen und den Container neu starten:

```bash
# .env
DB_PORT=5434
```

Wichtig: Der Port in `snippets/settings_db.py` muss dann ebenfalls auf 5434 geändert werden.
Ein anderer Port ist kein Fehler — die Übung nutzt bewusst 5433, um nicht mit einer lokal
installierten PostgreSQL auf 5432 zu kollidieren.

---

## 2. Container startet nicht / bleibt „unhealthy"

**Prüfen:**

```bash
docker compose ps
```

Zeigt `db` nicht `healthy`, sondern `starting` oder `unhealthy`, sagt das Log warum:

```bash
docker compose logs db
```

**Häufige Ursachen im Log:**

- `initdb: directory "/var/lib/postgresql/data" exists but is not empty` — ein abgebrochener
  Start hat Reste hinterlassen. Volume neu aufbauen:

  ```bash
  docker compose down -v
  docker compose up -d
  ```

  Achtung: `-v` löscht alle Daten. Fixture danach neu laden.

- `database system is starting up` in Schleife — einfach warten. Der erste Start initialisiert
  das Datenverzeichnis und braucht ein paar Sekunden. Der Healthcheck hat ein `start_period`
  von 10 Sekunden, in denen Fehlschläge nicht zählen.

- `permission denied` auf dem Datenverzeichnis — meist ein Volume-Konflikt aus einem anderen
  Projekt. Das benannte Volume heißt `bibliothek_db_data`; prüfen mit:

  ```bash
  docker volume ls | grep bibliothek
  ```

**Zustand direkt testen:**

```bash
docker compose exec db pg_isready -U bibliothek -d bibliothek
# /var/run/postgresql:5432 - accepting connections
```

---

## 3. „password authentication failed for user ..."

**Meldung (aus Django):**

```
django.db.utils.OperationalError: connection failed:
FATAL:  password authentication failed for user "bibliothek"
```

**Ursache 1 — `.env` fehlt oder weicht ab.** Die Datei wird nicht mitgeliefert:

```bash
cp .env.example .env
cat .env
```

PostgreSQL legt Benutzer und Passwort **nur beim allerersten Start** an. Wird `.env` danach
geändert, passt das Volume nicht mehr zur Konfiguration.

**Ursache 2 — genau dieses Auseinanderlaufen.** Die Lösung ist, die Datenbank neu aufzubauen:

```bash
docker compose down -v
cp .env.example .env
docker compose up -d
```

Danach Migration und Fixture neu:

```bash
python manage.py migrate
python manage.py loaddata demo
```

`-v` entfernt das Volume. Ohne `-v` bleibt der alte Benutzer bestehen und der Fehler kommt wieder.

**Gegenprobe, ob die Zugangsdaten stimmen:**

```bash
docker compose exec db psql -U bibliothek -d bibliothek -c "select current_user, current_database();"
```

---

## 4. Docker ist nicht installiert (SQLite-Ausweg)

Kein Docker und keine Zeit, es einzurichten? Die Übung läuft auch mit SQLite.

In `config/settings.py` den `DATABASES`-Block durch die **Variante 2** aus
`snippets/settings_db.py` ersetzen:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

Dann wie gewohnt:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata demo
```

**Was dabei anders ist:**

- Kein Adminer. Die Datenbank ist eine einzelne Datei `db.sqlite3`.
- Keine Benutzer und Passwörter — das entfällt als Fehlerquelle, ist aber auch nicht mehr Teil der Übung.
- SQL-Typen und Funktionen weichen von PostgreSQL ab. `print(qs.query)` sieht anders aus
  (Backticks statt Anführungszeichen in manchen Django-Versionen).
- Alle ORM-Aufgaben A1 bis A6 funktionieren gleich.

Für die Übung reicht das. Für das Verständnis von PostgreSQL nicht — wenn möglich, Docker nutzen.

---

## 5. „Fixture 'demo' not found"

**Meldung:**

```
django.core.management.base.CommandError: No database fixture specified.
Please provide the path of at least one fixture in the command line.
```

oder

```
CommandError: No fixture named 'demo' found.
```

**Ursache:** Django sucht Fixtures in drei Orten:

1. `<app>/fixtures/` — hier `bibliothek/fixtures/`
2. allen Verzeichnissen aus `FIXTURE_DIRS`
3. absoluten Pfaden

Die Datei liegt in `<projekt>/fixtures/demo.json` — also **weder** im App-Ordner **noch** ohne
Eintrag in `FIXTURE_DIRS` auffindbar.

**Lösung:** In `config/settings.py` ergänzen:

```python
FIXTURE_DIRS = [BASE_DIR / "fixtures"]
```

Der Block steht fertig in `snippets/settings_db.py`.

**Prüfen, ob es greift:**

```bash
python manage.py loaddata demo --verbosity 2
```

**Alternativ** den Pfad direkt angeben — zum Testen nützlich:

```bash
python manage.py loaddata fixtures/demo.json
```

Dabei auf das Arbeitsverzeichnis achten: der Befehl läuft relativ zum Ordner, in dem
`manage.py` liegt.

---

## 6. „no such table" / „relation ... does not exist" — Migration vergessen

**Meldung:**

```
django.db.utils.ProgrammingError: relation "bibliothek_buch" does not exist
```

oder beim Laden:

```
django.db.utils.ProgrammingError: Problem installing fixture: relation
"bibliothek_autor" does not exist
```

**Ursache:** Die Tabellen existieren nicht. Modelle in Python sind nur eine Beschreibung —
erst `makemigrations` erzeugt daraus eine Migration, `migrate` legt die Tabellen an.

**Lösung, immer in dieser Reihenfolge:**

```bash
python manage.py makemigrations bibliothek
python manage.py migrate
python manage.py loaddata demo
```

**Häufige Variante:** Du hast ein Feld ergänzt (Aufgabe A1) und danach nicht migriert:

```bash
python manage.py makemigrations bibliothek   # "Add field verlag to buch"
python manage.py migrate
```

**Kontrolle, ob die Tabelle da ist:**

```bash
python manage.py dbshell
# darin:
\dt bibliothek_*
```

**Kontrolle, ob die App registriert ist** — ohne sie kennt Django die Modelle nicht:

```python
# config/settings.py
INSTALLED_APPS = [
    # ...
    "bibliothek",
]
```

Fehlt der Eintrag, meldet `makemigrations` „No changes detected", obwohl Modelle existieren.
