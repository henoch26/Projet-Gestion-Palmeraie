from rest_framework import viewsets
from .models import Secteur
from .serializers import SecteurSerializer


class SecteurViewSet(viewsets.ModelViewSet):
    # CRUD complet pour les secteurs
    queryset = Secteur.objects.all().order_by("-id")
    serializer_class = SecteurSerializer
