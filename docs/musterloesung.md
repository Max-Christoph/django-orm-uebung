# Musterlösung — Aufgaben A1 bis A5

Alle Beispiele sind in der Django-Shell ausgeführt (`python manage.py shell`).
Voraussetzung: `python manage.py loaddata demo` ist gelaufen.

```python
from bibliothek.models import Autor, Kategorie, Buch
from django.db.models import Count, Avg, Max, Min, Q
```

---

## A1 — Feld `verlag` ergänzen

Die Modelle liegen in `bibliothek/models.py`. In `Buch` fehlt ein Feld — das ergänzt du jetzt.

**Modell anpassen** (`bibliothek/models.py`):

```python
class Buch(models.Model):
    titel = models.CharField(max_length=200)
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE, related_name="buecher")
    erscheinungsjahr = models.IntegerField()
    verlag = models.CharField(max_length=120, blank=True, default="")
    kategorien = models.ManyToManyField(Kategorie, related_name="buecher", blank=True)
```

`blank=True, default=""` ist wichtig: sonst verlangt die Migration einen Wert für die
bereits vorhandenen 400 Zeilen.

**Migration erzeugen und einspielen:**

```bash
python manage.py makemigrations bibliothek
python manage.py migrate
```

**Kontrolle:**

```python
Buch.objects.first().verlag        # '' -- Feld existiert, noch leer
Buch.objects.count()               # 400 -- Daten sind unverändert
```

---

## A2 — Filtern, Ordnen, Begrenzen

### Bücher von Kafka

```python
Buch.objects.filter(autor__name="Kafka")
```

`autor__name` folgt dem ForeignKey. Der doppelte Unterstrich (`__`) ist Djangos Weg,
über eine Beziehung zu filtern.

```python
Buch.objects.filter(autor__name="Kafka").count()
```

### Autoren vor 1900, alphabetisch

```python
Autor.objects.filter(geburtsjahr__lt=1900).order_by("name")
```

`__lt` heißt „less than" (`<`). Entsprechend: `__gt`, `__lte`, `__gte`, `__exact`.

### Die 10 neuesten Bücher

```python
Buch.objects.order_by("-erscheinungsjahr")[:10]
```

Ein Minus vor dem Feldnamen bedeutet absteigend. Die eckigen Klammern sind ein **LIMIT**,
kein Python-Slicing — Django setzt es in SQL um.

### Bücher vor 1900, älteste zuerst

```python
Buch.objects.filter(erscheinungsjahr__lt=1900).order_by("erscheinungsjahr")
```

---

## A3 — Aggregation und Gruppierung

### Wie viele Bücher, wie alt im Schnitt?

```python
Buch.objects.aggregate(anzahl=Count("id"), schnitt=Avg("erscheinungsjahr"))
# {'anzahl': 400, 'schnitt': 1884.5}
```

`aggregate()` liefert **ein** Ergebnis — ein Dictionary, keine Liste von Objekten.

### Ältestes und neuestes Erscheinungsjahr

```python
Buch.objects.aggregate(aeltestes=Min("erscheinungsjahr"), neuestes=Max("erscheinungsjahr"))
```

### Bücher pro Autor — die häufigste Falle

```python
Autor.objects.annotate(anzahl=Count("buecher")).order_by("-anzahl")
```

`annotate()` heißt: **pro Zeile** einen berechneten Wert anhängen — hier die Anzahl der
Bücher je Autor. Die Gruppierung entsteht automatisch.

`Count("buecher")` nutzt das `related_name` aus dem Modell, nicht `"buch"`.

Zugriff auf den berechneten Wert:

```python
for autor in Autor.objects.annotate(anzahl=Count("buecher")).order_by("-anzahl")[:5]:
    print(autor.name, autor.anzahl)
```

### Autoren mit mehr als 5 Büchern

```python
Autor.objects.annotate(anzahl=Count("buecher")).filter(anzahl__gt=5)
```

**Reihenfolge beachten:** Erst `annotate()`, dann `filter()`. Umgekehrt scheitert es, weil
der berechnete Wert beim Filtern noch nicht existiert.

### 10 Kategorien mit den meisten Büchern

```python
Kategorie.objects.annotate(anzahl=Count("buecher")).order_by("-anzahl")[:10]
```

**Ohne** `[:10]` bekommst du alle 12. Der Schnitt ist Teil der Aufgabe, nicht Kosmetik.

---

## A4 — Mit SQL-Ausgabe nachvollziehen

### `filter()` gegen `exclude()`

```python
Buch.objects.filter(autor__name="Kafka")
Buch.objects.exclude(autor__name="Kafka")
```

`exclude()` ist die Negation. Beide erzeugen unterschiedliches SQL:

```python
print(Buch.objects.filter(autor__name="Kafka").query)
print(Buch.objects.exclude(autor__name="Kafka").query)
```

Beachte das `NOT` und die andere Verschachtelung im zweiten Fall.

### Zwei Bedingungen: UND und ODER

```python
# UND -- beide Bedingungen müssen zutreffen
Buch.objects.filter(erscheinungsjahr__lt=1900, autor__name="Kafka")

# ODER -- eine genügt (Q-Objekte nötig)
Buch.objects.filter(Q(autor__name="Kafka") | Q(autor__name="Zweig"))
```

Mehrere Argumente in `filter()` sind immer mit **UND** verknüpft. Für **ODER** brauchst du
`Q`-Objekte: `|` für ODER, `&` für UND, `~` für NICHT.

Das erzeugt einen `JOIN`:

```python
print(Buch.objects.filter(autor__name="Kafka").query)
```

### Die N+1-Falle

So löst jede Zeile eine eigene Abfrage aus — 400 Bücher, 401 Abfragen:

```python
for buch in Buch.objects.all():
    print(buch.titel, buch.autor.name)
```

So nicht:

```python
for buch in Buch.objects.select_related("autor"):
    print(buch.titel, buch.autor.name)
```

`select_related()` für ForeignKey (ein JOIN), `prefetch_related()` für ManyToMany
(zwei Abfragen statt einer pro Zeile):

```python
for buch in Buch.objects.prefetch_related("kategorien"):
    print(buch.titel, [k.name for k in buch.kategorien.all()])
```

Mit `assertNumQueries` lässt sich die Zahl prüfen:

```python
from django.test.utils import CaptureQueriesContext
from django.db import connection

with CaptureQueriesContext(connection) as ctx:
    list(Buch.objects.select_related("autor"))

print(len(ctx.captured_queries))   # 1
```

---

## A5 — Löschen

Vorher zählen, damit du das Ergebnis einordnen kannst:

```python
Buch.objects.filter(erscheinungsjahr__lt=1900).count()
```

Löschen:

```python
Buch.objects.filter(erscheinungsjahr__lt=1900).delete()
```

Die Rückgabe nennt die Zahl der gelöschten Zeilen je Tabelle:

```python
# (Anzahl, {'bibliothek.Buch': Anzahl, 'bibliothek.Buch_kategorien': Anzahl})
```

Die **zweite** Zahl betrifft die m:n-Verknüpfungstabelle. Django räumt sie automatisch mit
auf — das ist die Aufgabe des ORM, nicht deine.

Danach prüfen:

```python
Buch.objects.filter(erscheinungsjahr__lt=1900).count()   # 0
Buch.objects.count()                                     # deutlich kleiner als 400
```

### Was passiert mit den Autoren?

```python
Autor.objects.count()      # unverändert 60
```

`on_delete=models.CASCADE` wirkt vom Autor zum **Buch**, nicht umgekehrt. Ein Autor
verschwindet nur, wenn der Autor selbst gelöscht wird — dann gehen seine Bücher mit.

```python
kafka = Autor.objects.get(name="Kafka")
kafka.buecher.count()      # Bücher, die noch übrig sind
```

---

## Bonus — die m:n-Beziehung

### Bücher einer Kategorie

```python
kategorie = Kategorie.objects.get(name="Roman")
kategorie.buecher.all()
```

`related_name="buecher"` erlaubt diesen Weg rückwärts. Ohne `related_name` wäre es
`buch_set`.

### Kategorien eines Buchs

```python
buch = Buch.objects.get(pk=1)
buch.kategorien.all()
```

### Bücher mit mehreren Kategorien

```python
Buch.objects.annotate(anzahl=Count("kategorien")).filter(anzahl__gte=2)
```

### Bücher einer Kategorie, die vor 1900 erschienen sind

```python
Buch.objects.filter(kategorien__name="Roman", erscheinungsjahr__lt=1900)
```

Zwei Bedingungen in einem `filter()` — wieder UND.

### Verknüpfung anlegen und lösen

```python
buch = Buch.objects.get(pk=1)
kategorie = Kategorie.objects.get(name="Essay")

buch.kategorien.add(kategorie)        # verknüpfen
buch.kategorien.remove(kategorie)     # lösen
buch.kategorien.set([1, 2, 3])        # komplett ersetzen (IDs oder Objekte)
```

---

## Zusatz A6 — das erzeugte SQL lesen

`print(qs.query)` zeigt das SQL eines **unevaluierten** QuerySets:

```python
qs = Buch.objects.filter(autor__name="Kafka")
print(qs.query)
```

Ausgabe (gekürzt):

```sql
SELECT "bibliothek_buch"."id", "bibliothek_buch"."titel", ...
FROM "bibliothek_buch"
INNER JOIN "bibliothek_autor" ON ("bibliothek_buch"."autor_id" = "bibliothek_autor"."id")
WHERE "bibliothek_autor"."name" = Kafka
```

Zum Lesen:

- Django benennt Tabellen `app_modell`, hier `bibliothek_buch`.
- Der ForeignKey wird zur Spalte `autor_id`, nicht `autor`.
- `autor__name` wird zum `INNER JOIN` plus `WHERE` — **nicht** zu einer zweiten Abfrage.
  Genau das ist der Unterschied zu `buch.autor.name` in einer Schleife (A4).
- Platzhalter `%s` erscheinen erst bei der Ausführung; das QuerySet ist noch nicht gelaufen.

Nützlich zum Prüfen, ob ein `select_related()` wirklich greift:

```python
print(Buch.objects.select_related("autor").filter(autor__name="Kafka").query)
```
