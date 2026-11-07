import json
from functools import lru_cache
from pathlib import Path

import numpy as np

from .features import clamp

ART = Path(__file__).resolve().parents[2] / "ml" / "artifacts"  # src/ml/artifacts
DEFAULT_META = {
    "numeric": ["amount", "transaction_hour", "foreign_transaction", "location_mismatch",
                "device_trust_score", "velocity_last_24h", "cardholder_age"],
    "categories": ["Clothing", "Electronics", "Food", "Grocery", "Travel"],
    "amount_p95": 500.0, "amount_max": 2000.0, "trained": False,
}


@lru_cache
def meta() -> dict:
    try:
        m = json.loads((ART / "meta.json").read_text())
        m["trained"] = True
        return m
    except Exception:
        return DEFAULT_META


@lru_cache
def load():
    """Returns (xgboost, isolation-forest bundle), or None if train.py has not been run."""
    try:
        import joblib
        return joblib.load(ART / "xgb.joblib"), joblib.load(ART / "iso.joblib")
    except Exception:
        return None


def vector(req):
    m = meta()
    nums = [float(getattr(req, n)) for n in m["numeric"]]
    cats = [1.0 if req.merchant_category == c else 0.0 for c in m["categories"]]
    return np.array([nums + cats], dtype=float)


def ml_score(req, f: dict) -> float:
    m = load()
    if m is None:  # heuristic fallback so the API still works untrained
        amt = clamp(req.amount / meta()["amount_p95"] * 50)
        return 0.3 * amt + 0.25 * f["geo"] + 0.25 * f["device"] + 0.2 * f["behavior"]
    xgb, iso = m
    x = vector(req)
    p = float(xgb.predict_proba(x)[0, 1])
    s = float(iso["model"].score_samples(x)[0])
    anomaly = min(1.0, max(0.0, (iso["hi"] - s) / (iso["hi"] - iso["lo"])))
    return 80 * p + 20 * anomaly  # supervised signal 80%, unsupervised anomaly 20%