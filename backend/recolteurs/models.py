from django.db import models


class Recolteur(models.Model):
    # Recolteur: personne qui recolte dans un secteur
    STATUT_CHOICES = [
        ("Actif", "Actif"),
        ("Inactif", "Inactif"),
    ]

    nom = models.CharField(max_length=120)
    contact = models.CharField(max_length=50, blank=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="Actif")
    # Lien optionnel vers un secteur (on garde nullable pour faciliter la saisie)
    secteur = models.ForeignKey(
        "secteurs.Secteur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recolteurs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom
