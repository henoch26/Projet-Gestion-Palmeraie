from rest_framework import viewsets
from .models import Recolteur
from .serializers import RecolteurSerializer


class RecolteurViewSet(viewsets.ModelViewSet):
    # CRUD complet pour les recolteurs
    queryset = Recolteur.objects.all().order_by("-id")
    serializer_class = RecolteurSerializer
