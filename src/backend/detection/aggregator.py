import math
from . import explain, features, ml, rules

WEIGHTS = {"ml": 0.50, "rules": 0.20, "behavior": 0.15, "device": 0.10, "geo": 0.05}
LABELS = {"ml": "ML model", "rules": "Rules", "behavior": "Behavior", "device": "Device", "geo": "Geography"}
TIERS = [
    ("Low", 30, "Approve automatically."),
    ("Medium", 60, "Verify with the customer and keep monitoring."),
    ("High", 80, "Hold the transaction and alert an analyst."),
    ("Critical", 100, "Block and open an investigation case."),
]


def tier_of(score: int):
    return next(t for t in TIERS if score <= t[1])


def aggregate(req) -> dict:
    f = features.build(req)
    signals = {
        "ml": ml.ml_score(req, f),
        "rules": rules.rule_score(req, ml.meta()["amount_p95"]),
        "behavior": f["behavior"],
        "device": f["device"],
        "geo": f["geo"],
    }
    parts = [{"label": LABELS[k], "points": WEIGHTS[k] * signals[k]} for k in WEIGHTS]
    score = round(sum(p["points"] for p in parts))
    name, _, action = tier_of(score)
    prob = round(100 / (1 + math.exp(-(score - 55) / 11)))
    return {"score": score, "probability": prob, "tier": name, "action": action, "parts": parts,
            "drivers": explain.drivers(req)}