import json
import pickle
from pathlib import Path
from datetime import date, timedelta
import calendar

from django.db.models import Sum
from django.utils import timezone

from secteurs.models import Secteur
from recolteurs.models import Recolteur
from recoltes.models import FicheRecolteDetail
from paiements.models import Paiement
from .models import ParametreIA

# Dossier d'artefacts (modele + meta)
ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "ia_model.pkl"
META_PATH = ARTIFACT_DIR / "ia_model_meta.json"

# Metriques ciblees par le modele
TARGETS = ["quantite", "montant_net", "rendement"]

# Valeurs par defaut (si parametres non renseignes)
PARAM_DEFAULTS = {
    "rainfall_mm": 200,
    "temperature_c": 26,
    "workforce_count": 100,
    "fertilizer_kg_ha": 80,
    "maintenance_index": 70,
    "nonconformity_pct": 3,
    "active_area_ha": 100,
}


# -----------------------------
# Outils date / periodes
# -----------------------------
def add_months(d, months):
    # Ajoute N mois en conservant un jour valide
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(d.day, last_day)
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


def end_of_period(start, freq):
    # Calcule la fin de periode a partir du debut
    if freq == "day":
        return start
    if freq == "week":
        return start + timedelta(days=6)
    if freq == "month":
        return add_months(start, 1) - timedelta(days=1)
    if freq == "quarter":
        return add_months(start, 3) - timedelta(days=1)
    if freq == "semester":
        return add_months(start, 6) - timedelta(days=1)
    if freq == "year":
        return add_months(start, 12) - timedelta(days=1)
    return start


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
# Construction du dataset
# -----------------------------
def compute_area_ref():
    # Superficie totale (fallback si non renseignee)
    area = sum(float(s.superficie_ha or 0) for s in Secteur.objects.all())
    return area if area > 0 else 100.0


def build_features(param, area_ref):
    # Construit un dict de features (numeriques + categoriels)
    start = align_start(param.date, param.frequency)
    sector_code = param.secteur.code if param.secteur else "GLOBAL"

    def val(x, default):
        return float(x) if x is not None else default

    return {
        "rainfall_mm": val(param.rainfall_mm, PARAM_DEFAULTS["rainfall_mm"]),
        "temperature_c": val(param.temperature_c, PARAM_DEFAULTS["temperature_c"]),
        "workforce_count": val(param.workforce_count, PARAM_DEFAULTS["workforce_count"]),
        "fertilizer_kg_ha": val(param.fertilizer_kg_ha, PARAM_DEFAULTS["fertilizer_kg_ha"]),
        "maintenance_index": val(param.maintenance_index, PARAM_DEFAULTS["maintenance_index"]),
        "nonconformity_pct": val(param.nonconformity_pct, PARAM_DEFAULTS["nonconformity_pct"]),
        "active_area_ha": val(param.active_area_ha, area_ref),
        "frequency": param.frequency,
        "sector_code": sector_code,
        "month": start.month,
        "quarter": (start.month - 1) // 3 + 1,
        "semester": 1 if start.month <= 6 else 2,
        "year": start.year,
        "week": start.isocalendar().week,
    }


def build_targets(param, area_ref):
    # Calcule les cibles reelles pour l'entrainement
    start = align_start(param.date, param.frequency)
    end = end_of_period(start, param.frequency)

    # Quantite recoltee (regimes) sur la periode
    qty_qs = FicheRecolteDetail.objects.filter(
        ligne__fiche__date__range=(start, end)
    )
    if param.secteur:
        qty_qs = qty_qs.filter(secteur=param.secteur)
    total_qty = qty_qs.aggregate(total=Sum("quantite"))["total"] or 0

    # Montant net des paiements sur la periode
    net_qs = Paiement.objects.filter(date__range=(start, end))
    if param.secteur:
        net_qs = net_qs.filter(secteur=param.secteur)
    total_net = net_qs.aggregate(total=Sum("net"))["total"] or 0

    # Rendement = quantite / superficie
    if param.secteur and param.secteur.superficie_ha:
        area = float(param.secteur.superficie_ha)
    else:
        area = float(param.active_area_ha or area_ref)
    if area <= 0:
        area = area_ref or 1.0
    rendement = total_qty / area

    return {
        "quantite": float(total_qty),
        "montant_net": float(total_net),
        "rendement": float(rendement),
    }


def build_dataset():
    # Construit X/y a partir des ParametreIA
    area_ref = compute_area_ref()
    rows = []
    for param in ParametreIA.objects.select_related("secteur").all():
        features = build_features(param, area_ref)
        targets = build_targets(param, area_ref)
        rows.append({"features": features, "targets": targets})
    return rows


# -----------------------------
# Entrainement / persistence
# -----------------------------
def train_model(min_rows=12):
    # Entraine et sauvegarde le modele ML
    # Imports locaux pour eviter un crash si scikit-learn n'est pas installe
    import numpy as np
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.multioutput import MultiOutputRegressor
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    rows = build_dataset()
    if len(rows) < min_rows:
        raise ValueError(f"Pas assez de donnees pour entrainer (min {min_rows}).")

    X = [r["features"] for r in rows]
    y = [[r["targets"][k] for k in TARGETS] for r in rows]

    pipeline = Pipeline(
        steps=[
            ("vec", DictVectorizer(sparse=False)),
            (
                "model",
                MultiOutputRegressor(
                    RandomForestRegressor(
                        n_estimators=200,
                        random_state=42,
                        max_depth=None,
                    )
                ),
            ),
        ]
    )

    pipeline.fit(X, y)
    preds = pipeline.predict(X)

    y_arr = np.array(y, dtype=float)
    pred_arr = np.array(preds, dtype=float)

    mae = mean_absolute_error(y_arr, pred_arr, multioutput="raw_values")
    rmse = np.sqrt(mean_squared_error(y_arr, pred_arr, multioutput="raw_values"))
    r2 = r2_score(y_arr, pred_arr, multioutput="uniform_average")
    sigma = np.std(y_arr - pred_arr, axis=0)

    meta = {
        "trained_at": timezone.now().isoformat(),
        "rows": len(rows),
        "targets": TARGETS,
        "features": pipeline.named_steps["vec"].get_feature_names_out().tolist(),
        "metrics": {
            "mae": {k: float(mae[i]) for i, k in enumerate(TARGETS)},
            "rmse": {k: float(rmse[i]) for i, k in enumerate(TARGETS)},
            "r2": float(r2),
        },
        "sigma": {k: float(sigma[i]) for i, k in enumerate(TARGETS)},
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


def load_model():
    # Charge le modele et ses metadonnees
    if not MODEL_PATH.exists() or not META_PATH.exists():
        return None, None
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        with open(META_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
        return model, meta
    except Exception:
        # Si le modele ne peut pas etre charge (lib manquante, fichier corrompu)
        return None, None


# -----------------------------
# Prediction ML
# -----------------------------
def compute_shares_from_history():
    # Calcule des parts historiques par dimension
    sector_totals = {}
    recolteur_totals = {}
    regime_totals = {}

    details = FicheRecolteDetail.objects.values(
        "quantite",
        "secteur__code",
        "secteur_code",
        "ligne__regime_type",
        "ligne__recolteur__nom",
        "ligne__recolteur_nom",
    )

    for d in details:
        qty = int(d.get("quantite") or 0)
        sector = d.get("secteur__code") or d.get("secteur_code") or "N/A"
        recolteur = d.get("ligne__recolteur__nom") or d.get("ligne__recolteur_nom") or "Sans nom"
        regime = d.get("ligne__regime_type") or "inconnu"

        sector_totals[sector] = sector_totals.get(sector, 0) + qty
        recolteur_totals[recolteur] = recolteur_totals.get(recolteur, 0) + qty
        regime_totals[regime] = regime_totals.get(regime, 0) + qty

    def shares(totals, keys):
        if not keys:
            return {}
        total = sum(totals.values())
        if total <= 0:
            return {k: 1 / len(keys) for k in keys}
        return {k: totals.get(k, 0) / total for k in keys}

    secteurs = [s.code for s in Secteur.objects.all()] or ["N/A"]
    recolteurs = list(Recolteur.objects.values_list("nom", flat=True)) or ["Sans nom"]
    regimes = ["grands", "moyens", "petits"]

    return (
        shares(sector_totals, secteurs),
        shares(recolteur_totals, recolteurs),
        shares(regime_totals, regimes),
        secteurs,
        recolteurs,
        regimes,
    )


def predict_with_model(payload):
    # Prediction via modele ML entrainne
    model, meta = load_model()
    if not model or not meta:
        raise RuntimeError("Modele ML indisponible")

    freq = payload.get("frequency", "month")
    start = payload.get("start_date")
    end = payload.get("end_date")

    today = timezone.now().date()
    start_date = date.fromisoformat(start) if start else align_start(today, freq)
    end_date = date.fromisoformat(end) if end else start_date

    targets = payload.get("targets") or TARGETS
    dimensions = payload.get("dimensions") or ["global", "secteur", "recolteur", "regime"]

    area_ref = compute_area_ref()
    params = payload.get("parameters") or {}

    # Parametres avec fallback
    def val(name):
        v = params.get(name)
        if v in ("", None):
            return PARAM_DEFAULTS[name]
        return float(v)

    base_params = {
        "rainfall_mm": val("rainfall_mm"),
        "temperature_c": val("temperature_c"),
        "workforce_count": val("workforce_count"),
        "fertilizer_kg_ha": val("fertilizer_kg_ha"),
        "maintenance_index": val("maintenance_index"),
        "nonconformity_pct": val("nonconformity_pct"),
        "active_area_ha": val("active_area_ha"),
    }

    # Serie de prediction globale (quantite, net, rendement)
    periods = generate_periods(start_date, end_date, freq)
    sigma = meta.get("sigma", {})

    def period_features(period_start):
        # Features par periode (avec date)
        return {
            **base_params,
            "frequency": freq,
            "sector_code": "GLOBAL",
            "month": period_start.month,
            "quarter": (period_start.month - 1) // 3 + 1,
            "semester": 1 if period_start.month <= 6 else 2,
            "year": period_start.year,
            "week": period_start.isocalendar().week,
        }

    X = [period_features(p["start"]) for p in periods]
    preds = model.predict(X)

    # Construction des series
    series = {k: [] for k in TARGETS}
    for idx, p in enumerate(periods):
        period_key = p["key"]
        pred = preds[idx]
        for i, target in enumerate(TARGETS):
            val = float(pred[i])
            s = float(sigma.get(target, 0))
            # Intervalle simple autour de la prediction
            min_v = max(0.0, val - s * 1.5)
            max_v = max(val, val + s * 1.5)
            series[target].append(
                {"period": period_key, "value": round(val, 2), "min": round(min_v, 2), "max": round(max_v, 2)}
            )

    # Construction des rows par dimension (shares historiques)
    rows = []
    secteur_shares, recolteur_shares, regime_shares, secteurs, recolteurs, regimes = compute_shares_from_history()

    def push_rows(target, dimension, key, value, min_v, max_v):
        rows.append(
            {
                "period": period_key,
                "dimension": dimension,
                "key": key,
                "metric": target,
                "value": round(value, 2),
                "min": round(min_v, 2),
                "max": round(max_v, 2),
            }
        )

    for p_idx, p in enumerate(periods):
        period_key = p["key"]
        qty = series["quantite"][p_idx]["value"]
        qty_min = series["quantite"][p_idx]["min"]
        qty_max = series["quantite"][p_idx]["max"]

        net = series["montant_net"][p_idx]["value"]
        net_min = series["montant_net"][p_idx]["min"]
        net_max = series["montant_net"][p_idx]["max"]

        rend = series["rendement"][p_idx]["value"]
        rend_min = series["rendement"][p_idx]["min"]
        rend_max = series["rendement"][p_idx]["max"]

        if "global" in dimensions:
            if "quantite" in targets:
                push_rows("quantite", "global", "TOTAL", qty, qty_min, qty_max)
            if "montant_net" in targets:
                push_rows("montant_net", "global", "TOTAL", net, net_min, net_max)
            if "rendement" in targets:
                push_rows("rendement", "global", "TOTAL", rend, rend_min, rend_max)

        if "secteur" in dimensions:
            for code in secteurs:
                share = secteur_shares.get(code, 0)
                if "quantite" in targets:
                    push_rows("quantite", "secteur", code, qty * share, qty_min * share, qty_max * share)
                if "montant_net" in targets:
                    push_rows("montant_net", "secteur", code, net * share, net_min * share, net_max * share)
                if "rendement" in targets:
                    push_rows("rendement", "secteur", code, rend * share, rend_min * share, rend_max * share)

        if "recolteur" in dimensions:
            for name in recolteurs:
                share = recolteur_shares.get(name, 0)
                if "quantite" in targets:
                    push_rows("quantite", "recolteur", name, qty * share, qty_min * share, qty_max * share)
                if "montant_net" in targets:
                    push_rows("montant_net", "recolteur", name, net * share, net_min * share, net_max * share)
                if "rendement" in targets:
                    push_rows("rendement", "recolteur", name, rend * share, rend_min * share, rend_max * share)

        if "regime" in dimensions:
            for reg in regimes:
                share = regime_shares.get(reg, 0)
                if "quantite" in targets:
                    push_rows("quantite", "regime", reg, qty * share, qty_min * share, qty_max * share)
                if "montant_net" in targets:
                    push_rows("montant_net", "regime", reg, net * share, net_min * share, net_max * share)
                if "rendement" in targets:
                    push_rows("rendement", "regime", reg, rend * share, rend_min * share, rend_max * share)

    return {
        "meta": {
            "engine": "ml",
            "trained_at": meta.get("trained_at"),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "frequency": freq,
            "targets": targets,
            "dimensions": dimensions,
            "metrics": meta.get("metrics", {}),
        },
        "parameters": base_params,
        "coefficients": {},
        "series": series,
        "rows": rows,
    }
