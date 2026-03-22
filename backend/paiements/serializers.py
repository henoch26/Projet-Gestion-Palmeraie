from django.utils import timezone
from rest_framework import serializers
from .models import Paiement


class PaiementSerializer(serializers.ModelSerializer):
    recolteur_nom = serializers.CharField(source="recolteur.nom", read_only=True)
    secteur_nom = serializers.CharField(source="secteur.nom", read_only=True)

    class Meta:
        model = Paiement
        fields = "__all__"

    def validate(self, attrs):
        # Calcul automatique du net (brut + bonus - penalite)
        instance = getattr(self, "instance", None)

        def num(field, default=0):
            if field in attrs:
                return float(attrs.get(field) or 0)
            if instance is not None:
                return float(getattr(instance, field) or 0)
            return float(default)

        brut = num("brut")
        bonus = num("bonus")
        penalite = num("penalite")
        net = brut + bonus - penalite
        if net < 0:
            raise serializers.ValidationError("Le montant net ne peut pas etre negatif")
        attrs["net"] = net

        # Statut "En retard" si date depassee et non paye/annule
        date_val = attrs.get("date") or (instance.date if instance else None)
        statut = attrs.get("statut") or (instance.statut if instance else "En attente")
        if date_val and statut in ("En attente", "En retard") and date_val < timezone.now().date():
            attrs["statut"] = "En retard"

        return attrs
