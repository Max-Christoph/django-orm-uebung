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
    # Achtung: "verlag" fehlt hier absichtlich -- das ist Uebung 1.
    kategorien = models.ManyToManyField(Kategorie, related_name="buecher", blank=True)

    def __str__(self):
        return self.titel
