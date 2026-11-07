import xgboost as xgb

from .ml import load, meta, vector

LABELS = {"amount": "Amount", "transaction_hour": "Hour of day", "foreign_transaction": "Foreign transaction",
          "location_mismatch": "Location mismatch", "device_trust_score": "Device trust",
          "velocity_last_24h": "Velocity (24h)", "cardholder_age": "Cardholder age"}


def drivers(req) -> list[dict]:
    """TreeSHAP values from XGBoost as each feature's signed share of influence (%).
    Positive pushes toward fraud. Merchant-category columns are merged into one driver.
    Empty list when the model has not been trained."""
    m = load()
    if m is None:
        return []
    contrib = m[0].get_booster().predict(xgb.DMatrix(vector(req)), pred_contribs=True)[0][:-1]
    numeric = meta()["numeric"]
    named = {LABELS.get(n, n): float(contrib[i]) for i, n in enumerate(numeric)}
    named["Merchant category"] = float(sum(contrib[len(numeric):]))
    total = sum(abs(v) for v in named.values()) or 1.0
    out = [{"feature": k, "impact": round(100 * v / total)} for k, v in named.items()]
    return sorted(out, key=lambda d: -abs(d["impact"]))