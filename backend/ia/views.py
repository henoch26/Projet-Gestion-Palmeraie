import calendar
import calendar
import math
from collections import defaultdict
from datetime import date, timedelta

from django.db.models import Sum
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from secteurs.models import Secteur
from recolteurs.models import Recolteur
from recoltes.models import FicheRecolteDetail
from paiements.models import Paiement
from .models import Anomalie, PredictionScenario, ParametreIA
from .serializers import AnomalieSerializer, PredictionScenarioSerializer, ParametreIASerializer
from .ml_engine import predict_with_model


# -----------------------------
# Utils date / periodes
# -----------------------------
def add_months(d, months):
    # Ajoute N mois en conservant un jour valide
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def align_start(d, freq):
    # Aligne la date sur le debut de periode
    if freq == "day":
        return d
    if freq == "week":
        return d - timedelta(days=d.weekday())
    if freq == "month":
        return d.replace(day=1)
    if freq == "quarter":
        month = ((d.month - 1) // 3) * 3 + 1
        return date(d.year, month, 1)
    if freq == "semester":
        month = 1 if d.month <= 6 else 7
        return date(d.year, month, 1)
    if freq == "year":
        return date(d.year, 1, 1)
    return d


def period_key(d, freq):
    # Clef lisible + clef de tri
    if freq == "day":
        return d.isoformat(), (d.year, d.month, d.day)
    if freq == "week":
        year, week, _ = d.isocalendar()
        return f"{year}-W{week:02d}", (year, week)
    if freq == "month":
        return f"{d.year}-{d.month:02d}", (d.year, d.month)
    if freq == "quarter":
        q = (d.month - 1) // 3 + 1
        return f"{d.year}-Q{q}", (d.year, q)
    if freq == "semester":
        s = 1 if d.month <= 6 else 2
        return f"{d.year}-S{s}", (d.year, s)
    if freq == "year":
        return f"{d.year}", (d.year, 1)
    return d.isoformat(), (d.year, d.month, d.day)


def generate_periods(start, end, freq):
    # Genere les periodes entre deux dates
    periods = []
    current = align_start(start, freq)
    while current <= end:
        key, sort_key = period_key(current, freq)
        periods.append({"key": key, "sort_key": sort_key, "start": current})
        if freq == "day":
            current += timedelta(days=1)
        elif freq == "week":
            current += timedelta(days=7)
        elif freq == "month":
            current = add_months(current, 1)
        elif freq == "quarter":
            current = add_months(current, 3)
        elif freq == "semester":
            current = add_months(current, 6)
        elif freq == "year":
            current = add_months(current, 12)
        else:
            current += timedelta(days=1)
    return periods


# -----------------------------
# Parametres et coefficients
# -----------------------------
PARAM_DEFAULTS = {
    "rainfall_mm": 200,        # Pluie (mm)
    "temperature_c": 26,       # Temperature moyenne (C)
    "workforce_count": 100,    # Main-d'oeuvre (nb de recolteurs)
    "fertilizer_kg_ha": 80,    # Engrais (kg/ha)
    "maintenance_index": 70,   # Entretien (0-100)
    "nonconformity_pct": 3,    # Non conformes (%)
    "active_area_ha": None,    # Superficie active (ha)
}


def build_default_coeffs(area_ref):
    # Coefficients par defaut (neutres si param = ref)
    return {
        "rainfall_mm": {"ref": 200, "weight": 0.12},
        "temperature_c": {"ref": 26, "weight": 0.10, "mode": "deviation"},
        "workforce_count": {"ref": 100, "weight": 0.08},
        "fertilizer_kg_ha": {"ref": 80, "weight": 0.10},
        "maintenance_index": {"ref": 70, "weight": 0.06},
        "nonconformity_pct": {"ref": 3, "weight": 0.20, "mode": "inverse"},
        # La superficie agit comme un facteur lineaire
        "active_area_ha": {"ref": area_ref, "weight": 1.0},
    }


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def merge_parameters(raw, area_ref):
    # Parametres du scenario (avec fallback sur les valeurs par defaut)
    params = dict(PARAM_DEFAULTS)
    params["active_area_ha"] = area_ref
    raw = raw or {}
    for k in params.keys():
        if k in raw and raw[k] not in ("", None):
            params[k] = safe_float(raw[k], params[k])
    return params


def merge_coeffs(raw, area_ref):
    # Coefficients utilises pour l'impact des parametres
    coeffs = build_default_coeffs(area_ref)
    raw = raw or {}
    for k, cfg in raw.items():
        if k not in coeffs:
            continue
        # On garde weight/ref si fournis
        ref = safe_float(cfg.get("ref"), coeffs[k]["ref"])
        weight = safe_float(cfg.get("weight"), coeffs[k]["weight"])
        mode = cfg.get("mode", coeffs[k].get("mode"))
        coeffs[k] = {"ref": ref, "weight": weight}
        if mode:
            coeffs[k]["mode"] = mode
    return coeffs


def compute_multiplier(params, coeffs):
    # Multiplie l'impact de chaque parametre
    mult = 1.0
    for key, cfg in coeffs.items():
        if key not in params:
            continue
        value = safe_float(params.get(key))
        ref = safe_float(cfg.get("ref"), 1.0)
        weight = safe_float(cfg.get("weight"), 0.0)
        if ref <= 0:
            continue

        mode = cfg.get("mode", "ratio")
        if mode == "deviation":
            # Penalise l'ecart a la reference (peu importe le sens)
            delta = abs(value - ref) / ref
            mult *= max(0.1, 1 - weight * delta)
        elif mode == "inverse":
            # Penalise une hausse au-dessus de la reference
            delta = (value - ref) / ref
            mult *= max(0.1, 1 - weight * delta)
        else:
            # Impact lineaire
            delta = (value - ref) / ref
            mult *= 1 + weight * delta

    return max(0.1, mult)


# -----------------------------
# Predicteur IA hybride
# -----------------------------
def collect_history(freq):
    # Rassemble les donnees historiques de quantite
    totals_by_period = defaultdict(int)
    sort_keys = {}
    sector_totals = defaultdict(int)
    recolteur_totals = defaultdict(int)
    regime_totals = defaultdict(int)

    details = (
        FicheRecolteDetail.objects.select_related("ligne__fiche", "secteur", "ligne__recolteur")
        .values(
            "ligne__fiche__date",
            "quantite",
            "secteur__code",
            "secteur_code",
            "ligne__regime_type",
            "ligne__recolteur__nom",
            "ligne__recolteur_nom",
        )
    )

    for d in details:
        dte = d.get("ligne__fiche__date")
        if not dte:
            continue
        key, sort_key = period_key(dte, freq)
        qty = int(d.get("quantite") or 0)
        totals_by_period[key] += qty
        sort_keys[key] = sort_key

        sector = d.get("secteur__code") or d.get("secteur_code") or "N/A"
        sector_totals[sector] += qty

        recolteur = d.get("ligne__recolteur__nom") or d.get("ligne__recolteur_nom") or "Sans nom"
        recolteur_totals[recolteur] += qty

        regime = d.get("ligne__regime_type") or "inconnu"
        regime_totals[regime] += qty

    return totals_by_period, sort_keys, sector_totals, recolteur_totals, regime_totals


def compute_trend(totals_by_period, sort_keys):
    # Calcule un trend simple sur les 12 derniers points
    if not totals_by_period:
        return 0.0, 0.0, 0.0

    # Serie ordonnee
    series = sorted(
        [(sort_keys[k], k, v) for k, v in totals_by_period.items()],
        key=lambda x: x[0],
    )
    values = [v for _, _, v in series][-12:]

    if len(values) == 1:
        return float(values[0]), 0.0, 0.0

    slope = (values[-1] - values[0]) / max(1, len(values) - 1)
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1)
    std = math.sqrt(var)
    return float(values[-1]), float(slope), float(std)


def compute_shares(totals, keys):
    # Convertit un total par cle en pourcentage (part)
    if not keys:
        return {}
    total = sum(totals.values())
    if total <= 0:
        return {k: 1 / len(keys) for k in keys}
    return {k: totals.get(k, 0) / total for k in keys}


def predict_series(periods, totals_by_period, base, slope, std, multiplier):
    # Genere la serie de prediction + intervalle min/max
    series = []
    last_val = base
    for p in periods:
        key = p["key"]
        if key in totals_by_period:
            last_val = totals_by_period[key]
        else:
            last_val = max(0, last_val + slope)

        val = last_val * multiplier
        uncertainty = max(std * 1.5, val * 0.08)
        series.append(
            {
                "period": key,
                "value": round(val, 2),
                "min": round(max(0, val - uncertainty), 2),
                "max": round(val + uncertainty, 2),
            }
        )
    return series


def build_predictions(payload):
    # -------- 1) Parametres de scenario --------
    freq = payload.get("frequency", "month")
    start = payload.get("start_date")
    end = payload.get("end_date")

    today = timezone.now().date()
    start_date = date.fromisoformat(start) if start else align_start(today, freq)
    # Par defaut: 6 periodes de projection
    if end:
        end_date = date.fromisoformat(end)
    else:
        # Ajoute 5 periodes au depart
        add = {"day": 5, "week": 5, "month": 5, "quarter": 5, "semester": 5, "year": 5}.get(freq, 5)
        end_date = start_date
        for _ in range(add):
            if freq == "day":
                end_date += timedelta(days=1)
            elif freq == "week":
                end_date += timedelta(days=7)
            elif freq == "month":
                end_date = add_months(end_date, 1)
            elif freq == "quarter":
                end_date = add_months(end_date, 3)
            elif freq == "semester":
                end_date = add_months(end_date, 6)
            elif freq == "year":
                end_date = add_months(end_date, 12)

    targets = payload.get("targets") or ["quantite", "montant_net", "rendement"]
    dimensions = payload.get("dimensions") or ["global", "secteur", "recolteur", "regime"]

    # Surface totale de reference
    secteur_list = list(Secteur.objects.all())
    area_ref = sum(float(s.superficie_ha or 0) for s in secteur_list)
    if area_ref <= 0:
        area_ref = 100.0

    params = merge_parameters(payload.get("parameters"), area_ref)
    coeffs = merge_coeffs(payload.get("coefficients"), area_ref)
    multiplier = compute_multiplier(params, coeffs)

    # -------- 2) Historique + trend --------
    totals_by_period, sort_keys, sector_totals, recolteur_totals, regime_totals = collect_history(freq)
    base, slope, std = compute_trend(totals_by_period, sort_keys)

    # -------- 3) Serie principale (quantite) --------
    periods = generate_periods(start_date, end_date, freq)
    quantite_series = predict_series(periods, totals_by_period, base, slope, std, multiplier)

    # -------- 4) Montant net (ratio net/quantite) --------
    total_net = Paiement.objects.aggregate(total=Sum("net"))["total"] or 0
    total_qty = sum(totals_by_period.values()) or 0
    # Ratio par defaut si aucune base
    net_ratio = float(total_net) / total_qty if total_qty > 0 else 1000.0

    # -------- 5) Rendement (quantite / superficie) --------
    area_total = params.get("active_area_ha") or area_ref
    if area_total <= 0:
        area_total = 1.0

    # -------- 6) Parts pour les dimensions --------
    secteurs_keys = [s.code for s in secteur_list] or ["N/A"]
    recolteurs_keys = list(Recolteur.objects.values_list("nom", flat=True)) or ["Sans nom"]
    regimes_keys = ["grands", "moyens", "petits"]

    secteur_shares = compute_shares(sector_totals, secteurs_keys)
    recolteur_shares = compute_shares(recolteur_totals, recolteurs_keys)
    regime_shares = compute_shares(regime_totals, regimes_keys)

    # -------- 7) Construction des rows --------
    rows = []
    series = {}

    # Serie globale (quantite)
    if "quantite" in targets:
        series["quantite"] = quantite_series
        if "global" in dimensions:
            for p in quantite_series:
                rows.append(
                    {
                        "period": p["period"],
                        "dimension": "global",
                        "key": "TOTAL",
                        "metric": "quantite",
                        "value": p["value"],
                        "min": p["min"],
                        "max": p["max"],
                    }
                )

    # Serie globale (montant_net)
    if "montant_net" in targets:
        montant_series = []
        for p in quantite_series:
            val = p["value"] * net_ratio
            min_v = p["min"] * net_ratio
            max_v = p["max"] * net_ratio
            montant_series.append(
                {"period": p["period"], "value": round(val, 2), "min": round(min_v, 2), "max": round(max_v, 2)}
            )
            if "global" in dimensions:
                rows.append(
                    {
                        "period": p["period"],
                        "dimension": "global",
                        "key": "TOTAL",
                        "metric": "montant_net",
                        "value": round(val, 2),
                        "min": round(min_v, 2),
                        "max": round(max_v, 2),
                    }
                )
        series["montant_net"] = montant_series

    # Serie globale (rendement)
    if "rendement" in targets:
        rendement_series = []
        for p in quantite_series:
            val = p["value"] / area_total
            min_v = p["min"] / area_total
            max_v = p["max"] / area_total
            rendement_series.append(
                {"period": p["period"], "value": round(val, 2), "min": round(min_v, 2), "max": round(max_v, 2)}
            )
            if "global" in dimensions:
                rows.append(
                    {
                        "period": p["period"],
                        "dimension": "global",
                        "key": "TOTAL",
                        "metric": "rendement",
                        "value": round(val, 2),
                        "min": round(min_v, 2),
                        "max": round(max_v, 2),
                    }
                )
        series["rendement"] = rendement_series

    # Dimensions: secteurs / recolteurs / regimes
    for p in quantite_series:
        period_key = p["period"]
        qty_val = p["value"]
        qty_min = p["min"]
        qty_max = p["max"]

        # Secteurs
        if "secteur" in dimensions:
            for code in secteurs_keys:
                share = secteur_shares.get(code, 0)
                val = qty_val * share
                min_v = qty_min * share
                max_v = qty_max * share
                if "quantite" in targets:
                    rows.append(
                        {
                            "period": period_key,
                            "dimension": "secteur",
                            "key": code,
                            "metric": "quantite",
                            "value": round(val, 2),
                            "min": round(min_v, 2),
                            "max": round(max_v, 2),
                        }
                    )
                if "montant_net" in targets:
                    rows.append(
                        {
                            "period": period_key,
                            "dimension": "secteur",
                            "key": code,
                            "metric": "montant_net",
                            "value": round(val * net_ratio, 2),
                            "min": round(min_v * net_ratio, 2),
                            "max": round(max_v * net_ratio, 2),
                        }
                    )
                if "rendement" in targets:
                    secteur_obj = next((s for s in secteur_list if s.code == code), None)
                    area = float(secteur_obj.superficie_ha or 0) if secteur_obj else 0
                    if area <= 0:
                        area = area_total * share if share > 0 else area_total
                    rows.append(
                        {
                            "period": period_key,
                            "dimension": "secteur",
                            "key": code,
                            "metric": "rendement",
                            "value": round(val / area, 2),
                            "min": round(min_v / area, 2),
                            "max": round(max_v / area, 2),
                        }
                    )

        # Recolteurs
        if "recolteur" in dimensions:
            for name in recolteurs_keys:
                share = recolteur_shares.get(name, 0)
                val = qty_val * share
                min_v = qty_min * share
                max_v = qty_max * share
                if "quantite" in targets:
                    rows.append(
                        {
                            "period": period_key,
                            "dimension": "recolteur",
                            "key": name,
                            "metric": "quantite",
                            "value": round(val, 2),
                            "min": round(min_v, 2),
                            "max": round(max_v, 2),
                        }
                    )
                if "montant_net" in targets:
                    rows.append(
                        {
                            "period": period_key,
                            "dimension": "recolteur",
                            "key": name,
                            "metric": "montant_net",
                            "value": round(val * net_ratio, 2),
                            "min": round(min_v * net_ratio, 2),
                            "max": round(max_v * net_ratio, 2),
                        }
                    )
                if "rendement" in targets:
                    area = area_total * share if share > 0 else area_total
                    rows.append(
                        {
                            "period": period_key,
                            "dimension": "recolteur",
                            "key": name,
                            "metric": "rendement",
                            "value": round(val / area, 2),
                            "min": round(min_v / area, 2),
                            "max": round(max_v / area, 2),
                        }
                    )

        # Regimes
        if "regime" in dimensions:
            for reg in regimes_keys:
                share = regime_shares.get(reg, 0)
                val = qty_val * share
                min_v = qty_min * share
                max_v = qty_max * share
                if "quantite" in targets:
                    rows.append(
                        {
                            "period": period_key,
                            "dimension": "regime",
                            "key": reg,
                            "metric": "quantite",
                            "value": round(val, 2),
                            "min": round(min_v, 2),
                            "max": round(max_v, 2),
                        }
                    )
                if "montant_net" in targets:
                    rows.append(
                        {
                            "period": period_key,
                            "dimension": "regime",
                            "key": reg,
                            "metric": "montant_net",
                            "value": round(val * net_ratio, 2),
                            "min": round(min_v * net_ratio, 2),
                            "max": round(max_v * net_ratio, 2),
                        }
                    )
                if "rendement" in targets:
                    area = area_total * share if share > 0 else area_total
                    rows.append(
                        {
                            "period": period_key,
                            "dimension": "regime",
                            "key": reg,
                            "metric": "rendement",
                            "value": round(val / area, 2),
                            "min": round(min_v / area, 2),
                            "max": round(max_v / area, 2),
                        }
                    )

    return {
        "meta": {
            "engine": "hybrid",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "frequency": freq,
            "targets": targets,
            "dimensions": dimensions,
        },
        "parameters": params,
        "coefficients": coeffs,
        "series": series,
        "rows": rows,
    }


# -----------------------------
# API
# -----------------------------
class AnomalieViewSet(viewsets.ModelViewSet):
    # CRUD complet pour les anomalies
    queryset = Anomalie.objects.all().order_by("-id")
    serializer_class = AnomalieSerializer


class PredictionScenarioViewSet(viewsets.ModelViewSet):
    # CRUD scenarios (historique)
    queryset = PredictionScenario.objects.all().order_by("-id")
    serializer_class = PredictionScenarioSerializer


class ParametreIAViewSet(viewsets.ModelViewSet):
    # CRUD parametres historiques pour futur entrainement ML
    queryset = ParametreIA.objects.all().order_by("-date", "-id")
    serializer_class = ParametreIASerializer


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def prediction_view(request):
    # GET: scenario par defaut
    # POST: scenario fourni par le front
    payload = request.data if request.method == "POST" else {}
    # Choix du moteur: ML si modele disponible, sinon hybride
    engine = payload.get("engine", "auto")
    use_ml = engine in ("ml", "auto")

    if use_ml:
        try:
            result = predict_with_model(payload)
        except RuntimeError:
            # Fallback si modele ML non disponible
            result = build_predictions(payload)
            result["meta"]["engine"] = "hybrid"
    else:
        result = build_predictions(payload)
        result["meta"]["engine"] = "hybrid"

    # Option: sauvegarde en base
    if request.method == "POST" and payload.get("save"):
        scenario = PredictionScenario.objects.create(
            name=payload.get("name", ""),
            start_date=date.fromisoformat(result["meta"]["start_date"]),
            end_date=date.fromisoformat(result["meta"]["end_date"]),
            frequency=result["meta"]["frequency"],
            targets=result["meta"]["targets"],
            dimensions=result["meta"]["dimensions"],
            parameters=result["parameters"],
            coefficients=result["coefficients"],
            result={"series": result["series"], "rows": result["rows"]},
        )
        result["scenario_id"] = scenario.id

    return Response(result)
