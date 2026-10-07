"""Laedt die Testdaten, aber nur wenn die Datenbank leer ist.

Aufruf:
    python manage.py seed

Warum als Management-Command und nicht als "loaddata demo" im Compose-Befehl:
Der Dienst "setup" laeuft bei jedem "docker compose up" erneut. Ein blankes
"loaddata demo" wuerde beim zweiten Mal mit doppelten Primary Keys abbrechen.
Dieser Befehl prueft vorher und tut dann nichts -- er ist idempotent.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand

from bibliothek.models import Autor, Buch, Kategorie


class Command(BaseCommand):
    help = "Laedt fixtures/demo.json, falls die Tabellen noch leer sind."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Daten auch dann laden, wenn schon Buecher vorhanden sind.",
        )

    def handle(self, *args, **options):
        vorhanden = Buch.objects.count()

        if vorhanden and not options["force"]:
            self.stdout.write(
                f"Datenbank enthaelt bereits {vorhanden} Buecher "
                f"({Autor.objects.count()} Autoren, {Kategorie.objects.count()} Kategorien) "
                "-- uebersprungen."
            )
            return

        if options["force"] and vorhanden:
            self.stdout.write(f"--force: lade trotz {vorhanden} vorhandener Buecher.")
            call_command("loaddata", "demo", verbosity=0)
            self.stdout.write(self.style.SUCCESS(
                f"Neu geladen: {Buch.objects.count()} Buecher."))
            return

        call_command("loaddata", "demo", verbosity=options.get("verbosity", 1))

        self.stdout.write(self.style.SUCCESS(
            f"Testdaten geladen: {Autor.objects.count()} Autoren, "
            f"{Buch.objects.count()} Buecher, {Kategorie.objects.count()} Kategorien."))
