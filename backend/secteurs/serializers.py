from rest_framework import serializers
from .models import Secteur


class SecteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Secteur
        fields = "__all__"
