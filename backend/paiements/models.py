from django.db import models
from django.utils import timezone


class Paiement(models.Model):
    STATUT_CHOICES = [
        ("Paye", "Paye"),
        ("En attente", "En attente"),
        ("En retard", "En retard"),
        ("Annule", "Annule"),
    ]

    date = models.DateField()
    recolteur = models.ForeignKey(
        "recolteurs.Recolteur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paiements",
    )
    secteur = models.ForeignKey(
        "secteurs.Secteur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paiements",
    )
    periode = models.CharField(max_length=60, blank=True)
    brut = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalite = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="En attente")
    reference = models.CharField(max_length=80, blank=True)
    commentaire = models.TextField(blank=True)
    # Archivage (historique)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement {self.id} - {self.statut}"

    def save(self, *args, **kwargs):
        # Enregistre d'abord pour obtenir l'id
        creating = self.pk is None
        super().save(*args, **kwargs)

        # Reference automatique si absente
        if not self.reference:
            year = self.date.year if self.date else timezone.now().year
            self.reference = f"PAY-{year}-{self.id:06d}"
            super().save(update_fields=["reference"])
