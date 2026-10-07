# django-orm-uebung

PostgreSQL und Testdaten für die Django-ORM-Übung.

**Du musst nichts konfigurieren. Das Projekt ist fertig eingerichtet — klonen, starten, üben.**

---

## Voraussetzungen

- **Docker** (getestet mit Docker 29.x und Docker Compose v5.x)
- **Python 3.10 oder neuer**

Prüfen:

```bash
docker --version && docker compose version
python --version
```

---

## Schnellstart

```bash
git clone https://github.com/Max-Christoph/django-orm-uebung.git && cd django-orm-uebung
docker compose up -d
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations && python manage.py migrate && python manage.py loaddata demo
python manage.py shell
```

In der Shell prüfen:

```python
from bibliothek.models import Autor, Buch, Kategorie
Autor.objects.count()      # 60
Buch.objects.count()       # 400
Kategorie.objects.count()  # 12
```

Fertig. **Es ist nichts einzurichten.** Keine `.env` anlegen, nichts in `settings.py`
bearbeiten, keine App registrieren.

Denke daran: Bei jeder neuen Shell-Sitzung muss die virtuelle Umgebung aktiv sein
(`source .venv/bin/activate`).

**Deine erste Änderung am Projekt ist Übung 1.**

Warum `makemigrations` dabeisteht: `bibliothek/migrations/` ist bewusst leer. Damit siehst du
einmal, woher die Tabellen kommen — `makemigrations` erzeugt aus den Modellen eine Migration,
`migrate` legt daraus die Tabellen an. Das `&&` sorgt dafür, dass der nächste Befehl nur läuft,
wenn der vorige geklappt hat.

---

## Was bereits eingerichtet ist

Damit du sofort mit dem ORM anfangen kannst, liegt das Projekt vollständig vor:

- `config/settings.py` — `INSTALLED_APPS` enthält `bibliothek`, `DATABASES` zeigt auf
  PostgreSQL `127.0.0.1:5433`, `FIXTURE_DIRS` zeigt auf `fixtures/`
- `bibliothek/models.py` — `Autor`, `Kategorie`, `Buch`
- `requirements.txt` — Django und psycopg
- `docker-compose.yml` — PostgreSQL 16 und Adminer, Zugangsdaten als Default

Fehlt noch etwas? Siehe `docs/troubleshooting.md`.

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

`Buch` fehlt ein Feld `verlag` (`CharField`, `max_length=120`). Ergänze es, erzeuge eine
Migration und spiele sie ein.

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
make up        # Datenbank und Adminer starten
make status    # Zustand der Container
make psql      # psql-Shell in der Datenbank
make logs      # Logs der Datenbank, mitlaufend
make down      # Container stoppen (Daten bleiben)
make reset     # Container stoppen UND Daten loeschen
```

Ohne `make`:

```bash
docker compose up -d
docker compose ps
docker compose exec db psql -U bibliothek -d bibliothek
docker compose down
docker compose down -v      # entfernt auch das Volume mit den Daten
```

---

## Adminer

Weboberfläche für die Datenbank: <http://localhost:8080>

Beim Anmelden:

- **System:** PostgreSQL
- **Server:** `db` (nicht `localhost` — aus Sicht des Containers heißt der Datenbankserver so)
- **Benutzername / Passwort / Datenbank:** `bibliothek`

Adminer ist zum Nachschauen nützlich. Die Übung selbst läuft über die Django-Shell.

---

## Zurücksetzen

Datenbank auf den Ausgangszustand bringen:

```bash
docker compose down -v
docker compose up -d
python manage.py migrate
python manage.py loaddata demo
```

`-v` entfernt das Volume — alle Daten sind weg, auch das `verlag`-Feld aus Übung 1. Die
Migration in `bibliothek/migrations/` bleibt erhalten, `makemigrations` brauchst du hier
also nicht erneut.

Nur die Daten neu laden, ohne die Datenbank neu zu bauen:

```bash
python manage.py loaddata demo
```

---

## Testdaten

`fixtures/demo.json` enthält 60 Autoren, 400 Bücher und 12 Kategorien mit 250
m:n-Verknüpfungen. Die Datei ist reproduzierbar — `scripts/make_fixture.py` erzeugt sie mit
festem Seed Byte für Byte identisch neu:

```bash
python scripts/make_fixture.py
```

Das Skript braucht kein Django und keine Datenbank, nur Python. Andere Größen:

```bash
python scripts/make_fixture.py --autoren 100 --buecher 800 --out /tmp/gross.json
```

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
├── docker-compose.yml         PostgreSQL 16 + Adminer
├── .env.example               optional, für eigene Zugangsdaten
├── Makefile                   Kurzbefehle
├── LICENSE                    MIT
├── README.md                  diese Datei
├── manage.py
├── requirements.txt           django, psycopg[binary]
├── config/                    Django-Projekt
│   ├── settings.py            fertig konfiguriert (PostgreSQL 5433, FIXTURE_DIRS)
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── bibliothek/                die App
│   ├── models.py              Autor, Kategorie, Buch
│   └── migrations/            noch leer — Übung 1 erzeugt die erste
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

---

## Lizenz

MIT — siehe `LICENSE`.
