FROM python:3.12-slim

# Keine .pyc-Dateien schreiben, Ausgaben sofort durchreichen -- so erscheinen
# Meldungen aus manage.py direkt in "docker compose logs".
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Erst nur die Abhaengigkeiten: diese Schicht bleibt im Cache, solange sich
# requirements.txt nicht aendert. Der zweite "docker compose up" ist dadurch
# sofort da.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Der Rest des Projekts. Beim Entwickeln wird /app ohnehin per Volume
# uebermounted (siehe docker-compose.yml) -- dieser Schritt macht das Image
# aber auch ohne Mount benutzbar.
COPY . .

# "web" schlaeft nur und wartet auf Befehle: docker compose exec web ...
CMD ["sleep", "infinity"]
