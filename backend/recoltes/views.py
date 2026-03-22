from rest_framework import viewsets
from .models import FicheRecolte
from .serializers import FicheRecolteSerializer


class FicheRecolteViewSet(viewsets.ModelViewSet):
    # CRUD complet pour les fiches de recolte (avec prefetch)
    queryset = FicheRecolte.objects.all().prefetch_related(
        "superviseurs_adjoints",
        "lignes__details",
        "recus",
    ).order_by("-id")
    serializer_class = FicheRecolteSerializer
