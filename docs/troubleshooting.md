# Troubleshooting

Sechs Probleme, die in der Übung praktisch immer auftreten — plus die Standardlösung.

Die Abschnitte sind nach Häufigkeit geordnet.

---

## 1. `service "web" is not running`

**Meldung:**

```
service "web" is not running
```

Das ist der häufigste Fehler. Er bedeutet: `web` läuft nicht — und fast immer liegt es daran,
dass **ein anderer Dienst den Start abgebrochen hat**.

**Immer zuerst nachsehen, was überhaupt läuft:**

```bash
docker compose ps -a
```

Die möglichen Fälle:

- `web` zeigt `Created` (nicht `Up`) → ein anderer Dienst konnte nicht starten. Siehe Problem 2.
- `setup` zeigt nicht `Exited (0)` → `setup` ist gescheitert und `web` wartet bewusst darauf.
  Siehe Problem 3.
- `db` ist nicht `healthy` → siehe Problem 5.
- Alles sieht gut aus, aber `exec` scheitert trotzdem → führe `docker compose up -d` erneut aus;
  beim zweiten Lauf startet `web` normalerweise nach.

**Prüfen, ob `web` nun läuft:**

```bash
docker compose ps
docker compose exec web python manage.py shell
```

---

## 2. „Port 8080 is already allocated"

**Meldung:**

```
Error response from daemon: failed to set up container networking: driver failed
programming external connectivity on endpoint bibliothek-adminer (...):
Bind for :::8080 failed: port is already allocated
```

**Ursache:** Auf Port 8080 läuft schon etwas anderes — ein Entwicklungsserver, ein anderes
Projekt oder ein bereits laufender Adminer.

Genau deshalb startet Adminer **nicht** mit `docker compose up -d`. Er liegt in einem eigenen
Profil, damit dieser Portkonflikt nicht den ganzen Start abreißt und `web` mit in den Abgrund
zieht.

**Prüfen, wer den Port hält:**

```bash
sudo lsof -i :8080
netstat -ano | findstr :8080        # Windows (PowerShell)
```

**Lösen:** Adminer auf einen anderen Port legen:

```bash
cp .env.example .env
# in .env: ADMINER_PORT=8081
docker compose --profile adminer up -d
```

Adminer ist dann unter <http://localhost:8081> erreichbar.

**Wenn du Adminer gar nicht brauchst**, ignoriere den Fehler. Die Datenbank und `web` sind
davon nicht betroffen — sie verbinden sich intern über `db:5432`.

---

## 3. „no such table" / „relation ... does not exist"

**Meldung:**

```
django.db.utils.ProgrammingError: relation "bibliothek_buch" does not exist
```

oder beim Laden der Daten:

```
django.db.utils.ProgrammingError: Problem installing fixture: relation
"bibliothek_autor" does not exist
```

**Ursache:** Die Tabellen fehlen. Beim Start legt der Dienst `setup` sie automatisch an — aber
nur, wenn er erfolgreich durchlief.

**Prüfen, was `setup` gemacht hat:**

```bash
docker compose logs setup
docker inspect --format='{{.State.ExitCode}}' bibliothek-setup
```

`ExitCode: 0` heißt erfolgreich. Das Log sollte enthalten:

```
Applying bibliothek.0001_initial... OK
Testdaten geladen: 60 Autoren, 400 Buecher, 12 Kategorien.
```

**Häufige Variante — Übung 1 bearbeitet, aber nicht migriert.** Nach dem Ändern von `models.py`
gehört dazu immer:

```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

Die Ausgabe von `makemigrations` sollte nennen:

```
Migrations for 'bibliothek':
  bibliothek/migrations/0002_buch_verlag.py
    - Add field verlag to buch
```

**Migrationen von Hand nachziehen:**

```bash
docker compose exec web python manage.py migrate
```

**Kontrolle, ob die Tabellen da sind:**

```bash
docker compose exec web python manage.py dbshell
# darin:
\dt bibliothek_*
```

**Sonderfall:** Läuft `migrate` durch, aber `makemigrations` meldet „No changes detected",
obwohl du `models.py` geändert hast — dann ist die App nicht registriert. Das ist hier bereits
eingerichtet, aber falls du `config/settings.py` angefasst hast:

```python
INSTALLED_APPS = [
    'bibliothek',
    # ...
]
```

---

## 4. „password authentication failed" oder „role does not exist"

**Meldung:**

```
django.db.utils.OperationalError: connection failed:
FATAL:  password authentication failed for user "bibliothek"
```

**Ursache 1 — `.env` liegt herum und weicht ab.** Normalerweise brauchst du keine `.env`: Die
Zugangsdaten stehen als Default in `docker-compose.yml`. Legst du aber eine an, gilt deren
Inhalt — auch bei Benutzer und Passwort.

```bash
ls -la .env
```

**Ursache 2 — Zugangsdaten nach dem ersten Start geändert.** PostgreSQL legt Benutzer und
Passwort **nur beim allerersten Start** an. Danach passt das Volume nicht mehr zur
Konfiguration. Ein Neustart hilft nicht, das Volume muss weg:

```bash
docker compose down -v
docker compose up -d
```

`-v` entfernt das Volume. Danach richtet `setup` alles neu ein — kein `migrate` von Hand nötig.

**Gegenprobe:**

```bash
docker compose exec db psql -U bibliothek -d bibliothek -c "select current_user, current_database();"
```

**Ursache 3 — `config/settings.py` wurde verändert.** Der Block liest die Werte aus der
Umgebung; die Defaults passen zum lokalen Weg. Im Container setzt `docker-compose.yml`
`POSTGRES_HOST=db` und `POSTGRES_PORT=5432`. Falls du dort etwas geändert hast, muss es so
aussehen:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'bibliothek'),
        'USER': os.environ.get('POSTGRES_USER', 'bibliothek'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'bibliothek'),
        'HOST': os.environ.get('POSTGRES_HOST', '127.0.0.1'),
        'PORT': os.environ.get('POSTGRES_PORT', '5433'),
    }
}
```

Wichtig: Der Host ist **`db`**, nicht `localhost` — aus Sicht der Container heißt der
Datenbankserver so.

---

## 5. Die Container starten nicht / `db` wird nicht `healthy`

**Prüfen:**

```bash
docker compose ps -a
docker compose logs db
```

**Häufige Ursachen im Log:**

- `initdb: directory "/var/lib/postgresql/data" exists but is not empty` — ein abgebrochener
  Start hat Reste hinterlassen. Volume neu aufbauen:

  ```bash
  docker compose down -v
  docker compose up -d
  ```

  Achtung: `-v` löscht alle Daten. `setup` richtet danach alles neu ein.

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

**Läuft `web` nicht, obwohl `setup` erfolgreich war?** Dann siehe Problem 1.

---

## 6. „Port 5433 is already allocated"

**Meldung:**

```
Bind for 0.0.0.0:5433 failed: port is already allocated
```

**Ursache:** Auf 5433 läuft schon etwas — meist ein älterer Container dieser Übung oder eine
PostgreSQL-Instanz, die jemand bewusst auf 5433 gelegt hat.

**Prüfen:**

```bash
sudo lsof -i :5433
sudo ss -tlnp | grep 5433        # Linux
netstat -ano | findstr :5433     # Windows
```

**Lösen:** Alten Container entfernen:

```bash
docker compose down
docker ps -a | grep bibliothek
```

Oder den Port verlegen:

```bash
cp .env.example .env
# in .env: DB_PORT=5434
docker compose up -d
```

Der Port 5433 ist nur für Werkzeuge **auf deinem Rechner** gedacht. Die Dienste `web` und
`setup` verbinden sich intern über `db:5432` und sind von diesem Problem nicht betroffen.

---

## Kurzübersicht

```bash
# Immer zuerst: was laeuft ueberhaupt? (-a zeigt auch gestoppte Container)
docker compose ps -a

# Wenn web nicht laeuft: woran scheiterte setup?
docker compose logs setup
docker inspect --format='{{.State.ExitCode}}' bibliothek-setup

# Wenn der Start mit einem Portfehler abbricht:
docker compose up -d                     # Fehlermeldung lesen

# Der Neustart von Null (loescht alle Daten)
docker compose down -v && docker compose up -d
```
