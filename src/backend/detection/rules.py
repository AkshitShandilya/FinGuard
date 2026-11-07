from .features import clamp

FLAG_AT = 40  # a rule score at or above this counts as "flagged" (used for the baseline in train.py)


def rule_score(req, amount_p95: float = 500.0) -> float:
    """Deterministic thresholds. Fast and auditable, blind to novel fraud."""
    s = 0
    s += 30 if req.amount >= amount_p95 else 0          # unusually large for this dataset
    s += 15 if req.transaction_hour <= 5 else 0         # night-time
    s += 20 if req.foreign_transaction else 0
    s += 20 if req.location_mismatch else 0
    s += 15 if req.device_trust_score < 40 else 0
    s += 15 if req.velocity_last_24h >= 5 else 0
    return clamp(s)