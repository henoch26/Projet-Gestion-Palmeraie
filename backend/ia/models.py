from django.db import models


class PredictionScenario(models.Model):
    # Scenario de prediction (parametres + resultats)
    FREQUENCY_CHOICES = [
        ("day", "Jour"),
        ("week", "Semaine"),
        ("month", "Mois"),
        ("quarter", "Trimestre"),
        ("semester", "Semestre"),
        ("year", "Annee"),
    ]

    name = models.CharField(max_length=120, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default="month")

    # Liste des metriques et dimensions demandees
    targets = models.JSONField(default=list)
    dimensions = models.JSONField(default=list)

    # Parametres du scenario (pluie, temperature, etc.)
    parameters = models.JSONField(default=dict)
    # Coefficients appliques (explicites pour garder la trace)
    coefficients = models.JSONField(default=dict)

    # Resultats stockes (series + tableaux)
    result = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Scenario {self.id}"


class ParametreIA(models.Model):
    # Parametres historiques pour entrainer un futur modele ML
    FREQUENCY_CHOICES = [
        ("day", "Jour"),
        ("week", "Semaine"),
        ("month", "Mois"),
        ("quarter", "Trimestre"),
        ("semester", "Semestre"),
        ("year", "Annee"),
    ]

    date = models.DateField()
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default="month")
    # Optionnel: on peut rattacher un secteur si besoin
    secteur = models.ForeignKey(
        "secteurs.Secteur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parametres_ia",
    )

    # Parametres (valeurs nulles autorisees si non connues)
    rainfall_mm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    temperature_c = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    workforce_count = models.PositiveIntegerField(null=True, blank=True)
    fertilizer_kg_ha = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    maintenance_index = models.PositiveIntegerField(null=True, blank=True)
    nonconformity_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    active_area_ha = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        secteur = self.secteur.code if self.secteur else "Global"
        return f"{self.frequency} - {self.date} - {secteur}"


class Anomalie(models.Model):
    NIVEAU_CHOICES = [
        ("Faible", "Faible"),
        ("Moyen", "Moyen"),
        ("Eleve", "Eleve"),
    ]

    date = models.DateField()
    type = models.CharField(max_length=120)
    zone = models.CharField(max_length=120)
    niveau = models.CharField(max_length=10, choices=NIVEAU_CHOICES, default="Moyen")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} ({self.niveau})"
