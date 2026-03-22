import calendar
from datetime import date

from django.db.models import Sum
from rest_framework.decorators import api_view
from rest_framework.response import Response

from secteurs.models import Secteur
from recolteurs.models import Recolteur
from recoltes.models import FicheRecolte, FicheRecolteDetail
from paiements.models import Paiement
from ia.models import Anomalie


@api_view(["GET"])
def summary_view(request):
    # Stats globales
    secteurs_count = Secteur.objects.count()
    recolteurs_actifs = Recolteur.objects.filter(statut="Actif").count()
    total_production = (
        FicheRecolteDetail.objects.aggregate(total=Sum("quantite"))["total"] or 0
    )
    rendement_moyen = round(
        total_production / secteurs_count, 2
    ) if secteurs_count else 0

    # Production mensuelle (6 derniers mois)
    today = date.today()
    labels = []
    data = []
    month = today.month
    year = today.year
    for _ in range(6):
        labels.append(calendar.month_abbr[month])
        total = (
            FicheRecolteDetail.objects.filter(
                ligne__fiche__date__year=year,
                ligne__fiche__date__month=month,
            ).aggregate(total=Sum("quantite"))["total"]
            or 0
        )
        data.append(total)
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    labels.reverse()
    data.reverse()

    # Performance recolteurs (top 5)
    perf = (
        FicheRecolteDetail.objects.values("ligne__recolteur_nom")
        .annotate(total=Sum("quantite"))
        .order_by("-total")[:5]
    )
    perf_labels = [p["ligne__recolteur_nom"] or "N/A" for p in perf]
    perf_data = [p["total"] for p in perf]

    # Prediction IA (simple: reel vs prevu)
    pred_labels = labels[-5:]
    pred_reel = data[-5:]
    pred_prevu = [max(0, int(v * 0.95)) for v in pred_reel]

    # Listes rapides
    secteurs_list = list(
        Secteur.objects.all().order_by("-id")[:5].values("code", "nom", "superficie_ha", "responsable")
    )
    recoltes_list = list(
        FicheRecolte.objects.all()
        .order_by("-date")[:5]
        .values("date")
    )
    paiements_list = list(
        Paiement.objects.all().order_by("-id")[:5].values("recolteur__nom", "net", "statut")
    )
    anomalies_list = list(
        Anomalie.objects.all().order_by("-id")[:5].values("type", "zone", "niveau")
    )

    return Response(
        {
            "stats": {
                "total_production": total_production,
                "secteurs_count": secteurs_count,
                "recolteurs_actifs": recolteurs_actifs,
                "rendement_moyen": rendement_moyen,
            },
            "charts": {
                "production_mensuelle": {"labels": labels, "data": data},
                "performance_recolteurs": {"labels": perf_labels, "data": perf_data},
                "prediction_ia": {"labels": pred_labels, "reel": pred_reel, "prevu": pred_prevu},
            },
            "lists": {
                "secteurs": secteurs_list,
                "recoltes": recoltes_list,
                "paiements": [
                    {
                        "recolteur": p["recolteur__nom"] or "-",
                        "net": p["net"],
                        "statut": p["statut"],
                    }
                    for p in paiements_list
                ],
                "anomalies": anomalies_list,
            },
        }
    )
