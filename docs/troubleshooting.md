# Troubleshooting

Sechs Probleme, die in der Übung praktisch immer auftreten — plus die Standardlösung.

Die ersten sechs Abschnitte sind nach Häufigkeit geordnet.

---

## 1. „no such table" / „relation ... does not exist" — Migration vergessen

**Meldung:**

```
django.db.utils.ProgrammingError: relation "bibliothek_buch" does not exist
```

oder beim Laden der Daten:

```
django.db.utils.ProgrammingError: Problem installing fixture: relation
"bibliothek_autor" does not exist
```

**Ursache:** Die Tabellen existieren nicht. Modelle in Python sind nur eine Beschreibung —
erst `makemigrations` erzeugt daraus eine Migration, `migrate` legt die Tabellen an.

Im Schnellstart steht `makemigrations` mit dabei, weil `bibliothek/migrations/` leer ist:

```bash
python manage.py makemigrations && python manage.py migrate && python manage.py loaddata demo
```

Das `&&` ist wichtig — läuft ein Schritt nicht durch, wird der nächste gar nicht erst versucht.
Führe die Befehle im Zweifel einzeln aus, dann siehst du, welcher scheitert.

**Lösung, immer in dieser Reihenfolge:**

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata demo
```

**Häufige Variante:** Du hast Übung 1 bearbeitet (Feld `verlag` ergänzt) und danach nicht
migriert:

```bash
python manage.py makemigrations bibliothek   # "Add field verlag to buch"
python manage.py migrate
```

**Kontrolle, ob die Tabellen da sind:**

```bash
python manage.py dbshell
# darin:
\dt bibliothek_*
```

**Sonderfall:** Läuft `migrate` durch, aber `makemigrations` meldet „No changes detected",
obwohl du `models.py` geändert hast — dann ist die App nicht registriert. Das ist hier bereits
eingerichtet (`INSTALLED_APPS` enthält `bibliothek`), aber falls du die Datei angefasst hast:

```python
# config/settings.py
INSTALLED_APPS = [
    'bibliothek',
    # ...
]
```

---

## 2. „password authentication failed" oder „role does not exist"

**Meldung (aus Django):**

```
django.db.utils.OperationalError: connection failed:
FATAL:  password authentication failed for user "bibliothek"
```

**Ursache 1 — `.env` liegt herum und weicht ab.** Normalerweise brauchst du keine `.env`: Die
Zugangsdaten stehen als Default in `docker-compose.yml`. Legst du aber eine `.env` an, gilt
deren Inhalt.

Prüfen, ob eine `.env` existiert:

```bash
ls -la .env
```

Gibt es eine und du brauchst sie nicht:

```bash
rm .env
docker compose down -v && docker compose up -d
python manage.py migrate
python manage.py loaddata demo
```

**Ursache 2 — die Zugangsdaten wurden nach dem ersten Start geändert.** PostgreSQL legt Benutzer
und Passwort **nur beim allerersten Start** an. Danach passt das Volume nicht mehr zur
Konfiguration. Ein Neustart hilft nicht, das Volume muss weg:

```bash
docker compose down -v
docker compose up -d
python manage.py migrate
python manage.py loaddata demo
```

`-v` entfernt das Volume. Ohne `-v` bleibt der alte Benutzer bestehen und der Fehler kommt wieder.

**Gegenprobe, ob die Zugangsdaten stimmen:**

```bash
docker compose exec db psql -U bibliothek -d bibliothek -c "select current_user, current_database();"
```

**Ursache 3 — `settings.py` wurde verändert.** Der `DATABASES`-Block ist fertig. Falls du dort
etwas angepasst hast, muss er so aussehen:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bibliothek',
        'USER': 'bibliothek',
        'PASSWORD': 'bibliothek',
        'HOST': '127.0.0.1',
        'PORT': '5433',
    }
}
```

---

## 3. Container startet nicht / bleibt „unhealthy"

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

  Achtung: `-v` löscht alle Daten. Danach `migrate` und `loaddata demo` erneut ausführen.

- `database system is starting up` in Schleife — einfach warten. Der erste Start initialisiert
  das Datenverzeichnis und braucht ein paar Sekunden. Der Healthcheck hat ein `start_period`
  von 10 Sekunden, in denen Fehlschläge nicht zählen.

- `permission denied` auf dem Datenverzeichnis — meist ein Volume-Konflikt aus einem anderen
  Projekt. Das benannte Volume heißt `bibliothek_db_data`:

  ```bash
  docker volume ls | grep bibliothek
  ```

**Zustand direkt testen:**

```bash
docker compose exec db pg_isready -U bibliothek -d bibliothek
# /var/run/postgresql:5432 - accepting connections
```

---

## 4. „Port 5433 is already allocated" / Port belegt

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

Bleibt der Port belegt, in `.env` einen anderen Wert setzen:

```bash
cp .env.example .env
# in .env: DB_PORT=5434
docker compose up -d
```

Wichtig: Dann muss auch `PORT` in `config/settings.py` auf `5434` geändert werden. Ein anderer
Port ist kein Fehler — die Übung nutzt bewusst 5433, um nicht mit einer lokal installierten
PostgreSQL auf 5432 zu kollidieren.

---

## 5. Docker ist nicht installiert (SQLite-Ausweg)

Kein Docker und keine Zeit, es einzurichten? Die Übung läuft auch mit SQLite.

In `config/settings.py` den `DATABASES`-Block ersetzen durch:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

Dann wie gewohnt:

```bash
python manage.py migrate
python manage.py loaddata demo
```

**Was dabei anders ist:**

- Kein Adminer. Die Datenbank ist eine einzelne Datei `db.sqlite3`.
- Keine Benutzer und Passwörter — das entfällt als Fehlerquelle, ist aber auch nicht mehr Teil
  der Übung.
- SQL-Typen und Funktionen weichen von PostgreSQL ab. `print(qs.query)` sieht anders aus.
- Beide Übungen funktionieren unverändert.

Für die Übung reicht das. Für das Verständnis von PostgreSQL nicht — wenn möglich, Docker nutzen.

---

## 6. „Fixture 'demo' not found"

**Meldung:**

```
CommandError: No fixture named 'demo' found.
```

**Ursache:** Django sucht Fixtures an drei Orten:

1. `<app>/fixtures/` — hier `bibliothek/fixtures/`
2. allen Verzeichnissen aus `FIXTURE_DIRS`
3. absoluten Pfaden

Die Datei liegt in `fixtures/demo.json`, also **weder** im App-Ordner **noch** ohne Eintrag in
`FIXTURE_DIRS` auffindbar.

In diesem Projekt ist das eingerichtet:

```python
FIXTURE_DIRS = [BASE_DIR / 'fixtures']
```

**Prüfen, ob die Zeile noch da ist:**

```bash
grep -n "FIXTURE_DIRS" config/settings.py
```

**Häufige Ursache:** Du führst den Befehl aus dem falschen Verzeichnis aus. `manage.py` muss im
aktuellen Ordner liegen:

```bash
ls manage.py
python manage.py loaddata demo
```

**Alternativ** den Pfad direkt angeben — zum Testen nützlich:

```bash
python manage.py loaddata fixtures/demo.json
```

**Kontrolle, ob die Datei überhaupt da ist:**

```bash
ls -la fixtures/demo.json
```

---

## Kurzübersicht

```bash
# Immer zuerst: laufen die Container?
docker compose ps

# Immer als Nächstes: was sagt die Datenbank?
docker compose logs db

# Der Neustart von Null (loescht alle Daten)
docker compose down -v && docker compose up -d
python manage.py migrate
python manage.py loaddata demo
```
