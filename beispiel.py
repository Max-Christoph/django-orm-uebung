"""Beispielskript fuer die Django-ORM-Uebung.

Zeigt, wie man das ORM aus einer eigenen Datei benutzt - ohne Shell.

Starten (im Projektordner, Container laeuft):
    docker compose exec web python beispiel.py

Die Zeilen unter "Django vorbereiten" braucht jedes eigene Skript, das
ausserhalb der Shell laeuft. Am einfachsten diese Datei kopieren und den
Teil ab "Los geht's" austauschen.
"""

# --- Django vorbereiten (muss in jedem eigenen Skript ganz oben stehen) ---
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# --- Modelle erst nach django.setup() importieren ---
from django.db.models import Avg, Count
from bibliothek.models import Autor, Buch, Kategorie

# --- Los geht's -----------------------------------------------------------

# 1) Zaehlen: passt der Datenbestand?
print("Autoren:   ", Autor.objects.count())
print("Buecher:   ", Buch.objects.count())
print("Kategorien:", Kategorie.objects.count())

# 2) Filtern: alle Buecher eines Autors
kafka = Buch.objects.filter(autor__name="Kafka").order_by("erscheinungsjahr")
print("\nBuecher von Kafka:")
for buch in kafka:
    print("  ", buch.titel, buch.erscheinungsjahr)

# 3) Aggregieren: ein Wert statt einer Liste
print("\nDurchschnittliches Erscheinungsjahr:")
print("  ", Buch.objects.aggregate(schnitt=Avg("erscheinungsjahr")))

# 4) Gruppieren: Buecher pro Autor
print("\nDie fuenf Autoren mit den meisten Buechern:")
for autor in Autor.objects.annotate(anzahl=Count("buecher")).order_by("-anzahl", "name")[:5]:
    print("  ", autor.name, "-", autor.anzahl)

# 5) Das erzeugte SQL ansehen
print("\nSQL der Kafka-Abfrage:")
print("  ", kafka.query)

# Schreiben funktioniert genauso - bitte auskommentiert lassen,
# damit die Testdaten unveraendert bleiben:
# Buch.objects.create(titel="Test", autor_id=1, erscheinungsjahr=2024)
