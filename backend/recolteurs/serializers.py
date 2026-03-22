from rest_framework import serializers
from .models import Recolteur


class RecolteurSerializer(serializers.ModelSerializer):
    secteur_nom = serializers.CharField(source="secteur.nom", read_only=True)

    class Meta:
        model = Recolteur
        fields = "__all__"
