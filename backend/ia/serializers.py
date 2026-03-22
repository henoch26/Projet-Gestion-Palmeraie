from rest_framework import serializers
from .models import Anomalie, PredictionScenario, ParametreIA


class AnomalieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anomalie
        fields = "__all__"


class PredictionScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionScenario
        fields = "__all__"


class ParametreIASerializer(serializers.ModelSerializer):
    secteur_code = serializers.CharField(source="secteur.code", read_only=True)
    secteur_nom = serializers.CharField(source="secteur.nom", read_only=True)

    class Meta:
        model = ParametreIA
        fields = "__all__"
