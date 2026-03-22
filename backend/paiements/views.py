from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.utils import timezone
from .models import Paiement
from .serializers import PaiementSerializer


class PaiementViewSet(viewsets.ModelViewSet):
    # CRUD complet pour les paiements
    queryset = Paiement.objects.all().order_by("-id")
    serializer_class = PaiementSerializer

    def get_queryset(self):
        # Par defaut: paiements actifs uniquement
        qs = Paiement.objects.all().order_by("-id")
        only_archived = self.request.query_params.get("only_archived") == "1"
        include_archived = self.request.query_params.get("include_archived") == "1"

        # Mise a jour automatique des paiements en retard
        today = timezone.now().date()
        Paiement.objects.filter(
            is_archived=False,
            statut__in=["En attente", "En retard"],
            date__lt=today,
        ).exclude(statut="Paye").update(statut="En retard")

        if only_archived:
            return qs.filter(is_archived=True)
        if include_archived:
            return qs
        return qs.filter(is_archived=False)

    def perform_update(self, serializer):
        # Blocage des modifications si paiement archive ou deja paye
        instance = self.get_object()
        if instance.is_archived:
            raise ValidationError("Paiement archive: modification interdite")
        if instance.statut in ("Paye", "Annule"):
            raise ValidationError("Paiement verrouille: modification interdite")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        # Archive au lieu de supprimer
        instance = self.get_object()
        if instance.statut != "Paye":
            raise ValidationError("Seuls les paiements payes peuvent etre archives")
        if not instance.is_archived:
            instance.is_archived = True
            instance.archived_at = timezone.now()
            instance.save(update_fields=["is_archived", "archived_at"])
        return Response(status=204)
