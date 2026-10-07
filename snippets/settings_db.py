# Fertige Konfigurationsbloecke fuer config/settings.py
#
# Kopiere den PostgreSQL-Block in deine config/settings.py und ersetze den
# vorhandenen DATABASES-Block. Der Port ist 5433 -- nicht 5432.

# ---------------------------------------------------------------------------
# Variante 1 (Standard): PostgreSQL aus docker compose
# ---------------------------------------------------------------------------
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "bibliothek"),
        "USER": os.environ.get("POSTGRES_USER", "bibliothek"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "bibliothek"),
        "HOST": "127.0.0.1",
        # 5433, damit eine lokal installierte PostgreSQL auf 5432 nicht stoert.
        "PORT": "5433",
    }
}


# ---------------------------------------------------------------------------
# Variante 2 (Ausweg ohne Docker): SQLite
# ---------------------------------------------------------------------------
# Funktioniert ueberall, hat aber kein PostgreSQL-Verhalten (kein eigenes
# Benutzer-/Rechtesystem, andere Typumwandlung). Fuer die Uebung ausreichend,
# wenn Docker auf dem Rechner nicht laeuft.
#
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }


# ---------------------------------------------------------------------------
# Fixture-Verzeichnis
# ---------------------------------------------------------------------------
# Damit "python manage.py loaddata demo" die Datei fixtures/demo.json findet,
# auch wenn sie nicht im App-Unterordner liegt.
FIXTURE_DIRS = [BASE_DIR / "fixtures"]
