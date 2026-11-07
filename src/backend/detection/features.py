def clamp(n: float) -> float:
    return max(0.0, min(100.0, n))


def build(req) -> dict:
    """Turns a request into the inputs for the Behavior, Device and Geography parts of the formula."""
    vel = clamp(req.velocity_last_24h * 20)               # 5+ transactions a day = 100
    night = 100 if req.transaction_hour <= 5 else 0       # 00:00 to 05:59
    return {
        "behavior": 0.6 * vel + 0.4 * night,
        "device": 100 - req.device_trust_score,           # low trust = high risk
        "geo": 50 * int(req.foreign_transaction) + 50 * int(req.location_mismatch),
    }