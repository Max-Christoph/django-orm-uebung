# django-orm-uebung

PostgreSQL und Testdaten für die Django-ORM-Übung (DHBW Karlsruhe).

**Dieses Repository enthält bewusst keinen Django-Projektcode.** Es liefert nur die Datenbank
(Docker Compose) und die Testdaten. Das Django-Projekt baust du im Vortrag selbst auf — Schritt
für Schritt, nach der Anleitung unten.

---

## Zweck

Wer das ORM verstehen will, braucht Daten, an denen sich etwas zeigen lässt: genug Zeilen für
sinnvolle Abfragen, Verknüpfungen über Fremdschlüssel und eine m:n-Beziehung. Genau das liegt
hier bereit — 60 Autoren, 400 Bücher, 12 Kategorien.

Die Übung ist so gebaut, dass die Datenbank **läuft, während du dein Projekt aufbaust**. Du
kümmerst dich nicht um Installation, Benutzer und Rechte von PostgreSQL, sondern nur um Django.

---

## Voraussetzungen

- **Docker** mit Compose (getestet mit Docker 29.x und Compose v5.x) — oder alternativ der
  SQLite-Ausweg, siehe `docs/troubleshooting.md`
- **Python 3.10 oder neuer** (`python --version`)
- **Django 5.x** und **psycopg 3** — werden gleich installiert
- Optional `make` für die Kurzbefehle

Prüfen, ob Docker läuft:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

---

## Schnellstart

Die Reihenfolge ist wichtig — erst die Datenbank, dann das Projekt.

```bash
git clone https://github.com/Max-Christoph/django-orm-uebung.git django-orm-uebung && cd django-orm-uebung
cp .env.example .env
docker compose up -d
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install django "psycopg[binary]"
django-admin startproject config .
python manage.py startapp bibliothek
```

Jetzt in `config/settings.py` zwei Dinge anpassen:

1. `"bibliothek"` in `INSTALLED_APPS` aufnehmen.
2. Den `DATABASES`-Block durch den PostgreSQL-Block aus `snippets/settings_db.py` ersetzen —
   **inklusive** `FIXTURE_DIRS`.

Dann:

```bash
python manage.py makemigrations && python manage.py migrate
python manage.py loaddata demo
python manage.py shell
```

In der Shell testen:

```python
from bibliothek.models import Autor, Buch, Kategorie
Autor.objects.count()      # 60
Buch.objects.count()       # 400
Kategorie.objects.count()  # 12
```

Läuft das, ist die Umgebung fertig.

---

## Die Modelle

Diese Modelle gehören in `bibliothek/models.py`. Sie sind verbindlich — die Testdaten passen
genau dazu.

```python
from django.db import models


class Autor(models.Model):
    name = models.CharField(max_length=100)
    geburtsjahr = models.IntegerField()

    def __str__(self):
        return self.name


class Kategorie(models.Model):
    name = models.CharField(max_length=60)

    def __str__(self):
        return self.name


class Buch(models.Model):
    titel = models.CharField(max_length=200)
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE, related_name="buecher")
    erscheinungsjahr = models.IntegerField()
    kategorien = models.ManyToManyField(Kategorie, related_name="buecher", blank=True)

    def __str__(self):
        return self.titel
```

**Ein Feld fehlt absichtlich:** `verlag`. Das ergänzt du in Aufgabe A1.

Die `__str__`-Methoden sind kein Beiwerk — ohne sie zeigt die Django-Shell und später der
Admin-Bereich `Buch object (1)` statt des Titels.

---

## Aufgaben

Die Musterlösung liegt in `docs/musterloesung.md`. Erst selbst probieren.

### A1 — Feld ergänzen

`Buch` fehlt ein Feld `verlag` (`CharField`, `max_length=120`). Ergänze es im Modell, erzeuge
eine Migration und spiele sie ein.

Achte darauf, dass die 400 vorhandenen Zeilen gültig bleiben — ohne Vorgabewert schlägt die
Migration fehl.

### A2 — Filtern, Ordnen, Begrenzen

1. Alle Bücher von Kafka.
2. Wie viele Bücher hat Kafka?
3. Alle Autoren mit Geburtsjahr vor 1900, alphabetisch nach Name.
4. Die 10 neuesten Bücher.
5. Alle Bücher vor 1900, älteste zuerst.

### A3 — Aggregation und Gruppierung

1. Wie viele Bücher gibt es, und wie alt sind sie im Durchschnitt?
2. Ältestes und neuestes Erscheinungsjahr.
3. Bücher pro Autor — absteigend sortiert.
4. Autoren mit mehr als 5 Büchern.
5. Die 10 Kategorien mit den meisten Büchern.

### A4 — Mit SQL-Ausgabe nachvollziehen

1. `filter()` gegen `exclude()` — beide für „Kafka", dann `print(qs.query)` für beide.
2. Zwei Bedingungen mit UND, dann zwei mit ODER (`Q`-Objekte).
3. Zeige das erzeugte SQL einer Abfrage mit Fremdschlüssel-Filter.
4. Warum löst eine Schleife über Bücher mit `buch.autor.name` so viele Abfragen aus?
   Zeige die Lösung mit `select_related()`.

### A5 — Löschen

1. Wie viele Bücher sind vor 1900 erschienen?
2. Lösche sie. Was gibt `delete()` zurück?
3. Wie viele Bücher bleiben übrig?
4. Was passiert mit den Autoren? Warum?

### Bonus — die m:n-Beziehung

1. Alle Bücher einer Kategorie.
2. Alle Kategorien eines Buchs.
3. Bücher mit mehr als einer Kategorie.
4. Alle Bücher der Kategorie „Roman", die vor 1900 erschienen sind.
5. Eine Verknüpfung anlegen und wieder lösen (`add`/`remove`/`set`).

### Zusatz A6 — das SQL lesen

Nimm eine beliebige Abfrage aus A3 oder A4 und erkläre Zeile für Zeile, was
`print(qs.query)` ausgibt. Warum heißt die Spalte `autor_id` und nicht `autor`?
Wo landet der Fremdschlüssel im SQL?

---

## Nützliche Befehle

```bash
make up        # Datenbank und Adminer starten
make status    # Zustand der Container
make psql      # psql-Shell in der Datenbank
make logs      # Logs der Datenbank, mitlaufend
make down      # Container stoppen (Daten bleiben)
make reset     # Container stoppen UND Daten löschen
make fixture   # fixtures/demo.json neu erzeugen
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
- **Benutzername / Passwort / Datenbank:** die Werte aus `.env`

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

`-v` entfernt das Volume — alle Daten sind weg, auch das `verlag`-Feld aus A1. Die Migrationen
in `bibliothek/migrations/` bleiben erhalten.

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

**Feste Ankerpunkte**, damit die Aufgaben immer dasselbe Ergebnis liefern:

- `pk 1` der Autoren ist **Kafka** (1883)
- `pk 1` der Bücher ist **Die Verwandlung** (1915)
- **Zweig** (1881) ist ebenfalls enthalten
- 225 Bücher sind vor 1900 erschienen — genug für Aufgabe A5
- 49 Autoren sind vor 1900 geboren

---

## Projektstruktur

```
django-orm-uebung/
├── docker-compose.yml        PostgreSQL 16 + Adminer
├── .env.example              Vorlage für die Zugangsdaten
├── Makefile                  Kurzbefehle
├── LICENSE                   MIT
├── README.md                 diese Datei
├── fixtures/
│   └── demo.json             Testdaten (60/400/12)
├── scripts/
│   └── make_fixture.py       erzeugt die Fixture neu
├── snippets/
│   └── settings_db.py        fertige DATABASES-Blöcke
└── docs/
    ├── musterlösung.md       Lösungen A1–A5, Bonus, A6
    └── troubleshooting.md    typische Fehler
```

**Kein Django-Code.** Kein `manage.py`, kein `settings.py`, keine `models.py`, keine
`migrations/`. Das ist Absicht: Du legst das Projekt selbst an und verstehst dadurch jeden
Schritt, statt eine fertige Vorlage zu öffnen.

---

## Was dieses Repository nicht ist

- Kein lauffähiges Django-Projekt — es ist die Datenbank dazu.
- Keine Produktionskonfiguration. Die Zugangsdaten in `.env.example` sind Übungswerte, für die
  lokale Entwicklung gedacht, nicht für einen erreichbaren Server.
- Keine vollständige Einführung ins ORM. Die Aufgaben sind der Rahmen, `docs/musterlösung.md`
  die Erklärung.

---

## Lizenz

MIT — siehe `LICENSE`.
