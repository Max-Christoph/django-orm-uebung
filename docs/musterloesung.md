# Musterlösung — Übung 1 und Übung 2

Alle Beispiele sind in der Django-Shell ausgeführt (`python manage.py shell`).
Voraussetzung: `python manage.py loaddata demo` ist gelaufen.

```python
from bibliothek.models import Autor, Kategorie, Buch
from django.db.models import Count, Avg, Max, Min
```

---

## Übung 1 — Feld `verlag` ergänzen

Das Modell liegt in `bibliothek/models.py`. In `Buch` fehlt ein Feld.

**Modell anpassen:**

```python
class Buch(models.Model):
    titel = models.CharField(max_length=200)
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE, related_name="buecher")
    erscheinungsjahr = models.IntegerField()
    verlag = models.CharField(max_length=120, blank=True, default="")
    kategorien = models.ManyToManyField(Kategorie, related_name="buecher", blank=True)
```

`blank=True, default=""` ist wichtig: In der Tabelle stehen bereits 400 Zeilen. Ohne Vorgabewert
verlangt die Migration für jede davon einen Wert und bricht ab.

**Migration erzeugen und einspielen:**

```bash
python manage.py makemigrations bibliothek
python manage.py migrate
```

Die Ausgabe von `makemigrations` sollte nennen:

```
Migrations for 'bibliothek':
  bibliothek/migrations/0001_initial.py
    ...
    - Add field verlag to buch
```

**Kontrolle in der Shell:**

```python
Buch.objects.first().verlag        # '' -- Feld existiert, noch leer
Buch.objects.count()               # 400 -- Daten unverändert
```

---

## Übung 2 — Abfragen

Voraussetzung: `python manage.py loaddata demo` ist gelaufen.

```python
from bibliothek.models import Autor, Kategorie, Buch
from django.db.models import Count, Avg, Max, Min
```

### 1. Alle Bücher von Kafka

```python
Buch.objects.filter(autor__name="Kafka")
```

`autor__name` folgt dem ForeignKey. Der doppelte Unterstrich (`__`) ist Djangos Weg, über eine
Beziehung zu filtern.

### 2. Wie viele Bücher hat Kafka?

```python
Buch.objects.filter(autor__name="Kafka").count()      # 12
```

`count()` erzeugt ein `SELECT count(*)`. **Nicht** `len(Buch.objects.filter(...))` schreiben —
das lädt alle Zeilen in den Speicher, um sie danach zu zählen.

### 3. Autoren mit Geburtsjahr vor 1900, alphabetisch

```python
Autor.objects.filter(geburtsjahr__lt=1900).order_by("name")     # 49 Autoren
```

`__lt` heißt „less than" (`<`). Entsprechend: `__gt`, `__lte`, `__gte`, `__exact`. Das Minus
für absteigende Sortierung wäre `order_by("-name")`.

### 4. Die 10 neuesten Bücher

```python
Buch.objects.order_by("-erscheinungsjahr")[:10]
```

Ein Minus vor dem Feldnamen bedeutet absteigend. Die eckigen Klammern sind ein **LIMIT**, kein
Python-Slicing — Django setzt es in SQL um:

```python
print(Buch.objects.order_by("-erscheinungsjahr")[:10].query)
# ... ORDER BY "bibliothek_buch"."erscheinungsjahr" DESC LIMIT 10
```

Ergebnis der Jahre: `[2020, 2020, 2020, 2019, 2019, 2017, 2016, 2016, 2016, 2012]`

### 5. Anzahl und Durchschnitt

```python
Buch.objects.aggregate(anzahl=Count("id"), schnitt=Avg("erscheinungsjahr"))
# {'anzahl': 400, 'schnitt': 1884.45}
```

`aggregate()` liefert **ein** Ergebnis — ein Dictionary, keine Liste von Objekten.

### 6. Ältestes und neuestes Erscheinungsjahr

```python
Buch.objects.aggregate(aeltestes=Min("erscheinungsjahr"), neuestes=Max("erscheinungsjahr"))
# {'aeltestes': 1750, 'neuestes': 2020}
```

### 7. Bücher pro Autor, absteigend

```python
Autor.objects.annotate(anzahl=Count("buecher")).order_by("-anzahl")
```

`annotate()` heißt: **pro Zeile** einen berechneten Wert anhängen — hier die Anzahl der Bücher je
Autor. Die Gruppierung entsteht automatisch. `Count("buecher")` nutzt das `related_name` aus dem
Modell.

Zugriff auf den berechneten Wert:

```python
for autor in Autor.objects.annotate(anzahl=Count("buecher")).order_by("-anzahl")[:5]:
    print(autor.name, autor.anzahl)
```

Der fleißigste Autor hat 15 Bücher.

Variante mit Filter — **Reihenfolge beachten**, erst `annotate()`, dann `filter()`. Umgekehrt
scheitert es, weil der berechnete Wert beim Filtern noch nicht existiert:

```python
Autor.objects.annotate(anzahl=Count("buecher")).filter(anzahl__gt=5)     # 36 Autoren
```

### 8. Das erzeugte SQL lesen

```python
qs = Buch.objects.filter(autor__name="Kafka")
print(qs.query)
```

Ausgabe:

```sql
SELECT "bibliothek_buch"."id", "bibliothek_buch"."titel", "bibliothek_buch"."autor_id",
       "bibliothek_buch"."erscheinungsjahr", "bibliothek_buch"."verlag"
FROM "bibliothek_buch"
INNER JOIN "bibliothek_autor" ON ("bibliothek_buch"."autor_id" = "bibliothek_autor"."id")
WHERE "bibliothek_autor"."name" = Kafka
```

Zum Lesen:

- Django benennt Tabellen `app_modell`, hier `bibliothek_buch`.
- Der ForeignKey wird zur Spalte **`autor_id`**, nicht `autor`. Django hängt `_id` an, weil die
  Spalte den Schlüsselwert speichert.
- `autor__name` wird zum **`INNER JOIN`** plus `WHERE` — **nicht** zu einer zweiten Abfrage. Genau
  das ist der Unterschied zu `buch.autor.name` in einer Schleife.
- Platzhalter für die Werte erscheinen erst bei der Ausführung; das QuerySet ist noch nicht gelaufen.

**Die N+1-Falle** — so löst jede Zeile eine eigene Abfrage aus (400 Bücher, 401 Abfragen):

```python
for buch in Buch.objects.all():
    print(buch.titel, buch.autor.name)          # eine Abfrage pro Buch
```

So nicht:

```python
for buch in Buch.objects.select_related("autor"):
    print(buch.titel, buch.autor.name)          # eine einzige Abfrage
```

`select_related()` für ForeignKey (ein JOIN), `prefetch_related()` für ManyToMany (zwei Abfragen
statt einer pro Zeile).

---

## Häufige Fehler

- **`annotate` und `filter` vertauscht** — erst `annotate()`, dann `filter()`.
- **`len(qs)` statt `qs.count()`** — lädt alle Zeilen, um sie zu zählen.
- **`Count("buch")`** statt `Count("buecher")` — das `related_name` entscheidet.
- **Zugriff außerhalb der Schleife** — `buch.autor.name` in einer Schleife ohne
  `select_related()` ist die klassische N+1-Falle.
