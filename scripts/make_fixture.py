#!/usr/bin/env python3
"""Erzeugt die Django-Fixture fixtures/demo.json fuer die ORM-Uebung.

Das Skript ist bewusst eigenstaendig:
  * keine Django-Imports
  * kein Datenbankzugriff
  * nur die Standardbibliothek

Es ist reproduzierbar: mit dem festen Seed entsteht bei jedem Lauf Byte fuer Byte dieselbe Datei.
Ohne Argumente wird genau die committete fixtures/demo.json neu erzeugt.

Verwendung:
    python scripts/make_fixture.py
    python scripts/make_fixture.py --autoren 100 --buecher 800 --out /tmp/gross.json
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

# Fester Seed -- nicht aendern, sonst weicht die committete Fixture ab.
SEED = 20260207

# Sollwerte der committeten Datei.
STANDARD_AUTOREN = 60
STANDARD_BUECHER = 400
STANDARD_KATEGORIEN = 12
STANDARD_VERKNUEPFUNGEN = 250

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
STANDARD_AUSGABE = REPO_DIR / "fixtures" / "demo.json"


# --------------------------------------------------------------------------- Stammdaten

KATEGORIEN = [
    "Roman",
    "Lyrik",
    "Drama",
    "Krimi",
    "Science-Fiction",
    "Fantasy",
    "Sachbuch",
    "Biografie",
    "Kinderbuch",
    "Horror",
    "Historischer Roman",
    "Essay",
]

# Klassiker mit korrekten Geburtsjahren. pk 1 MUSS Kafka mit 1883 sein.
AUTOREN_KLASSIKER = [
    ("Kafka", 1883),
    ("Zweig", 1881),
    ("Goethe", 1749),
    ("Schiller", 1759),
    ("Fontane", 1819),
    ("Heine", 1797),
    ("Storm", 1817),
    ("Keller", 1819),
    ("Stifter", 1805),
    ("Büchner", 1813),
    ("Hebbel", 1813),
    ("Mörike", 1804),
    ("Eichendorff", 1788),
    ("Novalis", 1772),
    ("Hölderlin", 1770),
    ("Kleist", 1777),
    ("Lessing", 1729),
    ("Wieland", 1733),
    ("Klopstock", 1724),
    ("Tieck", 1773),
    ("Brentano", 1778),
    ("Arnim", 1781),
    ("Chamisso", 1781),
    ("Droste-Hülshoff", 1797),
    ("Gotthelf", 1797),
    ("Raabe", 1831),
    ("Meyer", 1825),
    ("Ebner-Eschenbach", 1830),
    ("Hauptmann", 1862),
    ("Schnitzler", 1862),
    ("Hofmannsthal", 1874),
    ("Rilke", 1875),
    ("Mann", 1875),
    ("Hesse", 1877),
    ("Döblin", 1878),
    ("Trakl", 1887),
    ("Werfel", 1890),
    ("Musil", 1880),
    ("Broch", 1886),
    ("Roth", 1894),
    ("Fallada", 1893),
    ("Kästner", 1899),
    ("Brecht", 1898),
    ("Zuckmayer", 1896),
    ("Seghers", 1900),
    ("Böll", 1917),
    ("Grass", 1927),
    ("Walser", 1927),
    ("Süskind", 1949),
    ("Wolf", 1929),
]

# Namensbausteine fuer die uebrigen (frei erfundenen) Autoren.
NACHNAMEN_BAUSTEINE = [
    "Amsel", "Bergmann", "Brandt", "Dorn", "Eberhardt", "Falk", "Fischer", "Gerber",
    "Hahn", "Hartmann", "Hoffmann", "Kern", "Krause", "Lang", "Lehmann", "Lindner",
    "Meier", "Neumann", "Otto", "Pfeiffer", "Reuter", "Richter", "Sander", "Scholz",
    "Sommer", "Stein", "Thiele", "Vogel", "Wagner", "Weber", "Winkler", "Zander",
]

# Werkverzeichnis der Klassiker (Titel, Erscheinungsjahr, Autoren-pk).
BUECHER_KLASSIKER = [
    ("Die Verwandlung", 1915, 1),          # pk 1 -- verbindlich
    ("Der Prozess", 1925, 1),
    ("Das Urteil", 1913, 1),
    ("Die Welt von Gestern", 1942, 2),
    ("Schachnovelle", 1942, 2),
    ("Brief einer Unbekannten", 1922, 2),
    ("Faust", 1808, 3),
    ("Die Leiden des jungen Werthers", 1774, 3),
    ("Wilhelm Meisters Lehrjahre", 1795, 3),
    ("Die Räuber", 1781, 4),
    ("Kabale und Liebe", 1784, 4),
    ("Wallenstein", 1799, 4),
    ("Effi Briest", 1895, 5),
    ("Der Stechlin", 1898, 5),
    ("Der Schimmelreiter", 1888, 7),
    ("Der grüne Heinrich", 1854, 8),
    ("Romeo und Julia auf dem Dorfe", 1856, 8),
    ("Buch der Lieder", 1827, 6),
    ("Aus dem Leben eines Taugenichts", 1826, 13),
    ("Heinrich von Ofterdingen", 1802, 14),
    ("Hyperion", 1797, 15),
    ("Der zerbrochne Krug", 1811, 16),
    ("Michael Kohlhaas", 1810, 16),
    ("Nathan der Weise", 1779, 17),
    ("Emilia Galotti", 1772, 17),
    ("Woyzeck", 1837, 10),
    ("Dantons Tod", 1835, 10),
    ("Die Judenbuche", 1842, 24),
    ("Der Hungerpastor", 1864, 26),
    ("Der Heilige", 1880, 27),
    ("Die Weber", 1892, 29),
    ("Reigen", 1900, 30),
    ("Leutnant Gustl", 1900, 30),
    ("Der Tod des Tizian", 1892, 31),
    ("Die Weise von Liebe und Tod des Cornets", 1906, 32),
    ("Buddenbrooks", 1901, 33),
    ("Der Zauberberg", 1924, 33),
    ("Siddhartha", 1922, 34),
    ("Berlin Alexanderplatz", 1929, 35),
    ("Gedichte", 1913, 36),
    ("Der Mann ohne Eigenschaften", 1930, 38),
    ("Kleiner Mann - was nun?", 1932, 41),
    ("Fabian", 1931, 42),
    ("Die Dreigroschenoper", 1928, 43),
]

# Titelbausteine fuer die uebrigen (frei erfundenen) Werke.
TITEL_ARTIKEL = ["Der", "Die", "Das", "Ein", "Eine"]
TITEL_HAUPTWORT = [
    "Abschied", "Anfang", "Augenblick", "Brief", "Brücke", "Dorf", "Erinnerung", "Fahrt",
    "Fenster", "Fluss", "Garten", "Geschichte", "Glück", "Hafen", "Haus", "Herbst",
    "Hoffnung", "Insel", "Jahr", "Kind", "Kirche", "Lied", "Licht", "Morgen",
    "Nacht", "Regen", "Reise", "Schatten", "Schloss", "Sommer", "Spiegel", "Stadt",
    "Stimme", "Stunde", "Sturm", "Tag", "Traum", "Ufer", "Weg", "Winter",
]
TITEL_ZUSATZ = [
    "im Norden", "am Meer", "in den Bergen", "aus Papier", "ohne Namen", "der Dinge",
    "einer Freundschaft", "im Exil", "vor dem Krieg", "nach dem Regen", "in Blau",
    "aus Staub", "der verlorenen Zeit", "am Rand", "im Zwielicht", "einer Nacht",
]


# --------------------------------------------------------------------------- Erzeugung

def erzeuge_autoren(anzahl: int) -> list[dict]:
    """Autor-Datensaetze. pk 1 ist Kafka (1883), Zweig (1881) ist enthalten."""
    if anzahl < len(AUTOREN_KLASSIKER):
        autoren = AUTOREN_KLASSIKER[:anzahl]
    else:
        autoren = list(AUTOREN_KLASSIKER)

    if anzahl > len(autoren):
        rnd = random.Random(SEED + 1)
        pool = list(NACHNAMEN_BAUSTEINE)
        rnd.shuffle(pool)
        index = 0
        while len(autoren) < anzahl:
            nachname = pool[index % len(pool)]
            # Bei mehr Autoren als Bausteinen: durchnummerieren, damit die Namen eindeutig bleiben.
            runde = index // len(pool)
            if runde:
                nachname = f"{nachname}-{runde + 1}"
            geburtsjahr = rnd.randint(1800, 1985)
            autoren.append((nachname, geburtsjahr))
            index += 1

    return [
        {"model": "bibliothek.autor", "pk": pk, "fields": {"name": name, "geburtsjahr": jahr}}
        for pk, (name, jahr) in enumerate(autoren, start=1)
    ]


def erzeuge_kategorien(anzahl: int) -> list[dict]:
    return [
        {"model": "bibliothek.kategorie", "pk": pk, "fields": {"name": name}}
        for pk, name in enumerate(KATEGORIEN[:anzahl], start=1)
    ]


def erzeuge_buecher(anzahl: int, autor_anzahl: int, kategorien_anzahl: int,
                    verknuepfungen: int) -> list[dict]:
    """Buch-Datensaetze. pk 1 ist 'Die Verwandlung' (1915) von Kafka (pk 1)."""
    if anzahl < len(BUECHER_KLASSIKER):
        buecher = [t for t in BUECHER_KLASSIKER[:anzahl]]
    else:
        buecher = list(BUECHER_KLASSIKER)

    if anzahl > len(buecher):
        rnd = random.Random(SEED + 2)
        vorhandene_titel = {titel for titel, _, _ in buecher}
        while len(buecher) < anzahl:
            artikel = rnd.choice(TITEL_ARTIKEL)
            hauptwort = rnd.choice(TITEL_HAUPTWORT)
            zusatz = rnd.choice(TITEL_ZUSATZ)
            titel = f"{artikel} {hauptwort} {zusatz}"
            if titel in vorhandene_titel:
                continue
            vorhandene_titel.add(titel)
            buecher.append((titel, rnd.randint(1750, 2020), rnd.randint(1, autor_anzahl)))

    # Autoren-pk auf den gueltigen Bereich begrenzen (falls --autoren verkleinert wurde).
    buecher = [(titel, jahr, min(autor_pk, autor_anzahl)) for titel, jahr, autor_pk in buecher]

    # m:n-Verknuepfungen deterministisch und ohne Doppelungen verteilen.
    rnd = random.Random(SEED + 3)
    paare: set[tuple[int, int]] = set()
    # Didaktischer Anker: das erste Buch ("Die Verwandlung") bekommt verlaesslich eine
    # Kategorie, damit "Buch.objects.get(pk=1).kategorien.all()" nicht leer bleibt.
    if anzahl >= 1 and kategorien_anzahl >= 1:
        paare.add((1, 1))
    versuche = 0
    ziel = min(verknuepfungen, anzahl * kategorien_anzahl)
    while len(paare) < ziel and versuche < ziel * 50:
        versuche += 1
        buch_pk = rnd.randint(1, anzahl)
        kategorie_pk = rnd.randint(1, kategorien_anzahl)
        paare.add((buch_pk, kategorie_pk))

    zuordnung: dict[int, list[int]] = {}
    for buch_pk, kategorie_pk in sorted(paare):
        zuordnung.setdefault(buch_pk, []).append(kategorie_pk)

    datensaetze = []
    for pk, (titel, jahr, autor_pk) in enumerate(buecher, start=1):
        datensaetze.append({
            "model": "bibliothek.buch",
            "pk": pk,
            "fields": {
                "titel": titel,
                "autor": autor_pk,
                "erscheinungsjahr": jahr,
                "kategorien": sorted(zuordnung.get(pk, [])),
            },
        })
    return datensaetze


def baue_fixture(autoren: int, buecher: int) -> list[dict]:
    kategorien = erzeuge_kategorien(STANDARD_KATEGORIEN)
    # Verknuepfungen skalieren mit der Buchzahl; Standard 400 Buecher -> 250 Verknuepfungen.
    verknuepfungen = round(STANDARD_VERKNUEPFUNGEN * buecher / STANDARD_BUECHER)
    return (
        kategorien
        + erzeuge_autoren(autoren)
        + erzeuge_buecher(buecher, autoren, STANDARD_KATEGORIEN, verknuepfungen)
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Erzeugt die Django-Fixture fuer die Bibliotheks-Uebung.")
    parser.add_argument("--autoren", type=int, default=STANDARD_AUTOREN,
                        help=f"Anzahl Autoren (Standard: {STANDARD_AUTOREN})")
    parser.add_argument("--buecher", type=int, default=STANDARD_BUECHER,
                        help=f"Anzahl Buecher (Standard: {STANDARD_BUECHER})")
    parser.add_argument("--out", type=Path, default=STANDARD_AUSGABE,
                        help=f"Ausgabedatei (Standard: {STANDARD_AUSGABE})")
    args = parser.parse_args()

    daten = baue_fixture(args.autoren, args.buecher)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        json.dump(daten, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    buch_paare = sum(len(d["fields"]["kategorien"]) for d in daten if d["model"] == "bibliothek.buch")
    print(f"{args.out}: {len(daten)} Datensaetze")
    print(f"  Autoren:       {args.autoren}")
    print(f"  Buecher:       {args.buecher}")
    print(f"  Kategorien:    {STANDARD_KATEGORIEN}")
    print(f"  Verknuepfungen: {buch_paare}")
    print(f"  Buecher vor 1900: "
          f"{sum(1 for d in daten if d['model'] == 'bibliothek.buch' and d['fields']['erscheinungsjahr'] < 1900)}")


if __name__ == "__main__":
    main()
