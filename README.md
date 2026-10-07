# django-orm-uebung

PostgreSQL und Testdaten für die Django-ORM-Übung.

**Ein Befehl richtet alles ein: Datenbank, Tabellen und Testdaten. Du brauchst kein Python auf
deinem Rechner — nur Docker.**

---

## Voraussetzungen

- **Docker** (getestet mit Docker 29.x und Docker Compose v5.x)
- Internet beim **ersten** Start (das Image wird gebaut und Django heruntergeladen)

Prüfen:

```bash
docker --version && docker compose version
```

---

## Schnellstart

```bash
git clone https://github.com/Max-Christoph/django-orm-uebung.git && cd django-orm-uebung
docker compose up -d
docker compose exec web python manage.py shell
```

In der Shell prüfen:

```python
from bibliothek.models import Autor, Buch, Kategorie
Autor.objects.count()      # 60
Buch.objects.count()       # 400
Kategorie.objects.count()  # 12
```

Fertig. **Deine erste Änderung am Projekt ist Übung 1.**

Beim **ersten** `docker compose up -d` dauert es etwa eine Minute: Das Image wird gebaut und
Django installiert. Dabei laufen Meldungen wie `Downloading Django...`. Ab dem zweiten Mal
startet es in Sekunden, weil das Image im Cache liegt.

---

## Was beim Start passiert

`docker compose up -d` startet drei Dienste:

- **db** — PostgreSQL 16, Daten im benannten Volume
- **setup** — läuft **einmal**: `migrate` legt die Tabellen an, `seed` lädt die Testdaten.
  Danach beendet er sich.
- **web** — der Django-Container. Er startet erst, wenn `setup` **erfolgreich** durchgelaufen
  ist (`service_completed_successfully`). Dann wartet er auf deine Befehle.

Weil `setup` bei jedem `up` erneut läuft, ist `seed` idempotent: es lädt nur, wenn noch keine
Bücher in der Tabelle stehen. Der zweite Start wirft deshalb keine Fehler über doppelte
Primary Keys.

Prüfen, ob alles steht:

```bash
docker compose ps
```

`db` sollte `healthy` sein, `setup` mit `Exited (0)`, `web` mit `Up`.

**Adminer startet bewusst nicht mit.** Der Grund ist praktisch: Auf vielen Rechnern ist Port
8080 schon belegt (Entwicklungsserver, anderes Projekt). Das würde `docker compose up -d`
abbrechen lassen — und dann startet `web` nicht mehr, sodass jeder Befehl mit
`service "web" is not running` scheitert. Deshalb liegt Adminer in einem eigenen Profil:

```bash
docker compose --profile adminer up -d        # Adminer zusätzlich starten
# oder
make adminer
```

Ist 8080 bei dir belegt, lege eine `.env` an und ändere den Port:

```bash
cp .env.example .env
# in .env: ADMINER_PORT=8081
```

---

## So arbeitest du

Du editierst deine `.py`-Dateien **auf deinem Rechner** mit einem beliebigen Editor. Der Ordner
ist in den Container gemountet — deine Änderungen sind dort sofort wirksam. Danach führst du
Befehle im Container aus:

```bash
docker compose exec web python manage.py shell
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

Mit `make` wird es kürzer:

```bash
make shell
make makemigrations
make migrate
```

---

## Eigenes Skript ausführen

Alles Zeile für Zeile in der Shell einzutippen wird schnell mühsam. Sobald du eine längere
Abfrage ausprobierst, schreibe sie in eine Datei — dann kannst du sie ändern und neu starten,
ohne alles neu zu tippen.

Im Projektordner liegt dafür `beispiel.py`. Starten:

```bash
docker compose exec web python beispiel.py
```

Erwartete Ausgabe:

```
Autoren:    60
Buecher:    400
Kategorien: 12

Buecher von Kafka:
   Die Herbst einer Nacht 1760
   Der Abschied im Norden 1788
   Die Lied in den Bergen 1790
   Ein Nacht im Norden 1855
   Ein Haus einer Freundschaft 1856
   Das Urteil 1913
   Die Verwandlung 1915
   Eine Jahr einer Nacht 1919
   Der Prozess 1925
   Der Kirche einer Nacht 1976
   Eine Stadt der verlorenen Zeit 2012
   Eine Dorf der verlorenen Zeit 2017

Durchschnittliches Erscheinungsjahr:
   {'schnitt': 1884.45}

Die fuenf Autoren mit den meisten Buechern:
   Lessing - 15
   Reuter - 13
   Fontane - 12
   Kafka - 12
   Mann - 12

SQL der Kafka-Abfrage:
   SELECT "bibliothek_buch"."id", "bibliothek_buch"."titel", "bibliothek_buch"."autor_id",
          "bibliothek_buch"."erscheinungsjahr" FROM "bibliothek_buch"
          INNER JOIN "bibliothek_autor" ON ("bibliothek_buch"."autor_id" = "bibliothek_autor"."id")
          WHERE "bibliothek_autor"."name" = Kafka
          ORDER BY "bibliothek_buch"."erscheinungsjahr" ASC
```

Zur Orientierung, was das Skript zeigt:

- **Zählen** — 60 / 400 / 12, der Datenbestand stimmt
- **Filtern** — alle Bücher von Kafka, nach Erscheinungsjahr sortiert
- **Aggregieren** — `aggregate()` liefert einen einzelnen Wert (1884.45), keine Liste
- **Gruppieren** — `annotate()` hängt jedem Autor eine berechnete Zahl an
- **SQL ansehen** — `print(qs.query)` zeigt die echte Datenbankabfrage
- Am Ende steht ein auskommentiertes `create()`: Schreiben geht genauso, ist aber
  absichtlich deaktiviert, damit die Testdaten unverändert bleiben.

### Der Kopf ist Pflicht

Jedes eigene Skript braucht diese Zeilen **ganz oben**:

```python
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# erst jetzt die Modelle importieren
from bibliothek.models import Autor, Buch, Kategorie
```

`os.environ.setdefault(...)` sagt Django, welche Einstellungsdatei gilt — hier
`config/settings.py`. `django.setup()` lädt die Apps und die Datenbankverbindung. **Ohne diese
beiden Zeilen scheitern die Modell-Importe** mit:

```
django.core.exceptions.ImproperlyConfigured: Requested setting INSTALLED_APPS,
but settings are not configured.
```

Die Reihenfolge ist ebenfalls wichtig: `django.setup()` muss **vor** den Modell-Imports stehen,
sonst sind die Modelle noch nicht registriert.

Wenn du `beispiel.py` kopierst, tausch nur den Teil unter `# --- Los geht's ---` aus.

Das Skript mit `make` ausführen:

```bash
make run F=beispiel.py
make run F=mein_skript.py
```

`F` ist der Dateiname im Projektordner.

### Alternative: alles in der Shell

Wenn du nur kurz eine einzelne Zeile ausprobieren willst, brauchst du keine Datei:

```bash
docker compose exec web python manage.py shell
```

Das ist derselbe Python-Interpreter mit demselben Django-Kontext — nur Zeile für Zeile statt
als Datei. Für längere Abfragen ist ein Skript aber übersichtlicher, weil du es behalten und
wiederholen kannst.

---

## Die Modelle

`bibliothek/models.py`:

```python
class Autor(models.Model):
    name = models.CharField(max_length=100)
    geburtsjahr = models.IntegerField()

class Kategorie(models.Model):
    name = models.CharField(max_length=60)

class Buch(models.Model):
    titel = models.CharField(max_length=200)
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE, related_name="buecher")
    erscheinungsjahr = models.IntegerField()
    kategorien = models.ManyToManyField(Kategorie, related_name="buecher", blank=True)
```

Die Testdaten passen genau dazu.

---

## Übungen

Die Lösungen liegen in `docs/musterlösung.md`. Erst selbst probieren.

### Übung 1 — Feld ergänzen

`Buch` fehlt ein Feld `verlag` (`CharField`, `max_length=120`). Ergänze es in `models.py`, dann:

```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

Beachte: In der Tabelle stehen bereits 400 Zeilen. Ohne Vorgabewert bricht die Migration ab.

### Übung 2 — Abfragen

1. Alle Bücher von Kafka.
2. Wie viele Bücher hat Kafka?
3. Alle Autoren mit Geburtsjahr vor 1900, alphabetisch nach Name.
4. Die 10 neuesten Bücher.
5. Wie viele Bücher gibt es insgesamt, und wie hoch ist das durchschnittliche
   Erscheinungsjahr?
6. Ältestes und neuestes Erscheinungsjahr.
7. Bücher pro Autor, absteigend sortiert.
8. Lass dir zu einer der Abfragen mit `print(qs.query)` das erzeugte SQL ausgeben.
   Erkläre, was du siehst.

---

## Nützliche Befehle

```bash
make up        # alles starten (db, setup, web)
make shell     # Django-Shell im Container
make run F=x.py # eigenes Skript im Container ausfuehren
make adminer   # Adminer zusätzlich starten (http://localhost:8080)
make status    # Zustand der Container
make logs      # Logs, mitlaufend
make psql      # psql in der Datenbank
make down      # Container stoppen (Daten bleiben)
make reset     # Container stoppen UND Daten loeschen
```

Ohne `make`:

```bash
docker compose up -d
docker compose ps -a
docker compose exec web python manage.py shell
docker compose exec web python beispiel.py
docker compose exec db psql -U bibliothek -d bibliothek
docker compose --profile adminer up -d adminer     # Adminer zusätzlich
docker compose down
docker compose down -v      # entfernt auch das Volume mit den Daten
```

**Nach dem Ändern von `models.py`** gehört dazu immer:

```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

---

## Adminer

Weboberfläche für die Datenbank: <http://localhost:8080>

Beim Anmelden:

- **System:** PostgreSQL
- **Server:** `db` (nicht `localhost` — aus Sicht der Container heißt der Datenbankserver so)
- **Benutzername / Passwort / Datenbank:** `bibliothek`

---

## Zurücksetzen

```bash
docker compose down -v
docker compose up -d
```

`-v` entfernt das Volume — alle Daten sind weg, auch das `verlag`-Feld aus Übung 1. Danach
richtet `setup` die Datenbank automatisch neu ein. Es ist kein `migrate` von Hand nötig.

Nur die Daten neu laden, ohne alles neu zu bauen:

```bash
docker compose exec web python manage.py seed --force
```

---

## Alternative ohne Container-Django

Falls du Django lieber direkt auf deinem Rechner laufen lässt (oder kein Docker zur Verfügung
steht), geht es auch klassisch. Dafür brauchst du **Python 3.10 oder neuer**.

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
docker compose up -d db                                # nur die Datenbank
python manage.py migrate
python manage.py loaddata demo
python manage.py shell
```

Wichtig: `config/settings.py` verbindet sich standardmäßig mit `127.0.0.1:5433` — also mit der
Datenbank aus dem Container, erreichbar über den veröffentlichten Port. Genau dafür ist 5433
gewählt: eine bereits installierte PostgreSQL auf 5432 stört nicht.

**Ganz ohne Docker** — dann mit SQLite. In `config/settings.py` den `DATABASES`-Block ersetzen:

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

Was dabei anders ist: kein Adminer, keine Benutzer und Passwörter, und `print(qs.query)` sieht
anders aus. Beide Übungen funktionieren unverändert.

---

## Testdaten

`fixtures/demo.json` enthält 60 Autoren, 400 Bücher und 12 Kategorien mit 250
m:n-Verknüpfungen. Die Datei ist reproduzierbar — `scripts/make_fixture.py` erzeugt sie mit
festem Seed Byte für Byte identisch neu:

```bash
python scripts/make_fixture.py
```

Das Skript ist das einzige, das lokales Python braucht. Es läuft ohne Django und ohne Datenbank.

**Feste Ankerpunkte**, damit die Übungen immer dasselbe Ergebnis liefern:

- `pk 1` der Autoren ist **Kafka** (1883)
- `pk 1` der Bücher ist **Die Verwandlung** (1915), Kategorie „Roman"
- **Zweig** (1881) ist ebenfalls enthalten
- 225 Bücher sind vor 1900 erschienen
- 49 Autoren sind vor 1900 geboren

---

## Projektstruktur

```
django-orm-uebung/
├── Dockerfile                 python:3.12-slim, Django + psycopg
├── docker-compose.yml         db, setup, web (adminer nur mit Profil)
├── .env.example               optional, für eigene Zugangsdaten
├── Makefile                   Kurzbefehle
├── LICENSE                    MIT
├── README.md                  diese Datei
├── beispiel.py                Beispielskript: ORM aus einer eigenen Datei
├── manage.py
├── requirements.txt           django, psycopg[binary]
├── config/                    Django-Projekt
│   ├── settings.py            PostgreSQL, Port aus der Umgebung
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── bibliothek/                die App
│   ├── models.py              Autor, Kategorie, Buch
│   ├── migrations/            0001_initial.py
│   └── management/
│       └── commands/
│           └── seed.py        Testdaten laden, nur wenn leer
├── fixtures/
│   └── demo.json              Testdaten (60/400/12)
├── scripts/
│   └── make_fixture.py        erzeugt die Fixture neu
└── docs/
    ├── musterlösung.md        Lösungen zu beiden Übungen
    └── troubleshooting.md     sechs typische Fehler
```

---

## Hinweise

- Die Zugangsdaten `bibliothek`/`bibliothek` sind Übungswerte für die lokale Entwicklung,
  nicht für einen erreichbaren Server.
- `.env` wird nicht committet (steht in `.gitignore`).
- Port **5433** statt 5432, damit eine lokal installierte PostgreSQL auf 5432 nicht stört.
- Der `web`-Container ist kein Webserver — er wartet auf deine Befehle. Dafür ist
  `command: sleep infinity` da.

---

## Lizenz

MIT — siehe `LICENSE`.
