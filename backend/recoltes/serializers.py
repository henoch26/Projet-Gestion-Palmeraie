from django.db import transaction
from rest_framework import serializers
from .models import (
    FicheRecolte,
    SuperviseurAdjoint,
    FicheRecolteLigne,
    FicheRecolteDetail,
    FicheRecuVente,
)


class SuperviseurAdjointSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuperviseurAdjoint
        fields = ["id", "nom", "secteur_ou_recolteur"]


class FicheRecolteDetailSerializer(serializers.ModelSerializer):
    secteur_code = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = FicheRecolteDetail
        fields = ["id", "secteur", "secteur_code", "quantite"]


class FicheRecolteLigneSerializer(serializers.ModelSerializer):
    details = FicheRecolteDetailSerializer(many=True)
    recolteur_nom_display = serializers.CharField(source="recolteur.nom", read_only=True)
    paye_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = FicheRecolteLigne
        fields = [
            "id",
            "recolteur",
            "recolteur_nom",
            "recolteur_nom_display",
            "regime_type",
            "paye_amount",
            "details",
        ]

    def validate(self, attrs):
        # Au moins un identifiant de recolteur
        if not attrs.get("recolteur") and not attrs.get("recolteur_nom"):
            raise serializers.ValidationError("recolteur ou recolteur_nom requis")
        return attrs


class FicheRecuVenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FicheRecuVente
        fields = ["id", "date", "client", "pesee_kg", "non_conformes_pct", "montant"]


class FicheRecolteSerializer(serializers.ModelSerializer):
    superviseurs_adjoints = SuperviseurAdjointSerializer(many=True, required=False)
    lignes = FicheRecolteLigneSerializer(many=True, required=False)
    recus = FicheRecuVenteSerializer(many=True, required=False)

    class Meta:
        model = FicheRecolte
        fields = "__all__"

    def _compute_paye_amount(self, regime_type, details, bareme):
        # Calcule PAYE = total regimes * bareme
        total = sum(int(d.get("quantite") or 0) for d in details)
        rate = bareme.get(regime_type, 0)
        return total * rate

    @transaction.atomic
    def create(self, validated_data):
        superviseurs_data = validated_data.pop("superviseurs_adjoints", [])
        lignes_data = validated_data.pop("lignes", [])
        recus_data = validated_data.pop("recus", [])

        bareme = {
            "grands": validated_data.get("bareme_grands", 0),
            "moyens": validated_data.get("bareme_moyens", 0),
            "petits": validated_data.get("bareme_petits", 0),
        }

        fiche = FicheRecolte.objects.create(**validated_data)

        # Superviseurs adjoints
        for sup in superviseurs_data:
            SuperviseurAdjoint.objects.create(fiche=fiche, **sup)

        # Lignes + details
        for ligne in lignes_data:
            details = ligne.pop("details", [])

            # Snapshot du nom si recolteur existe
            recolteur = ligne.get("recolteur")
            if recolteur and not ligne.get("recolteur_nom"):
                ligne["recolteur_nom"] = recolteur.nom

            # PAYE calcule automatiquement (on ignore toute valeur envoyee)
            regime_type = ligne.get("regime_type")
            ligne["paye_amount"] = self._compute_paye_amount(regime_type, details, bareme)

            line = FicheRecolteLigne.objects.create(fiche=fiche, **ligne)
            for det in details:
                secteur = det.get("secteur")
                if secteur and not det.get("secteur_code"):
                    det["secteur_code"] = secteur.code
                FicheRecolteDetail.objects.create(ligne=line, **det)

        # Recus de vente
        for recu in recus_data:
            FicheRecuVente.objects.create(fiche=fiche, **recu)

        return fiche

    @transaction.atomic
    def update(self, instance, validated_data):
        superviseurs_data = validated_data.pop("superviseurs_adjoints", None)
        lignes_data = validated_data.pop("lignes", None)
        recus_data = validated_data.pop("recus", None)

        # Mise a jour des champs simples
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        bareme = {
            "grands": instance.bareme_grands,
            "moyens": instance.bareme_moyens,
            "petits": instance.bareme_petits,
        }

        # Remplacement complet des listes si fournies
        if superviseurs_data is not None:
            instance.superviseurs_adjoints.all().delete()
            for sup in superviseurs_data:
                SuperviseurAdjoint.objects.create(fiche=instance, **sup)

        if lignes_data is not None:
            instance.lignes.all().delete()
            for ligne in lignes_data:
                details = ligne.pop("details", [])
                recolteur = ligne.get("recolteur")
                if recolteur and not ligne.get("recolteur_nom"):
                    ligne["recolteur_nom"] = recolteur.nom
                regime_type = ligne.get("regime_type")
                ligne["paye_amount"] = self._compute_paye_amount(regime_type, details, bareme)
                line = FicheRecolteLigne.objects.create(fiche=instance, **ligne)
                for det in details:
                    secteur = det.get("secteur")
                    if secteur and not det.get("secteur_code"):
                        det["secteur_code"] = secteur.code
                    FicheRecolteDetail.objects.create(ligne=line, **det)

        if recus_data is not None:
            instance.recus.all().delete()
            for recu in recus_data:
                FicheRecuVente.objects.create(fiche=instance, **recu)

        return instance
