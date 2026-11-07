from detection.aggregator import WEIGHTS, aggregate
from schemas import ScoreRequest

NORMAL = dict(amount=40, transaction_hour=14, merchant_category="Grocery", foreign_transaction=False,
              location_mismatch=False, device_trust_score=85, velocity_last_24h=1, cardholder_age=40)
RISKY = dict(amount=100000, transaction_hour=3, merchant_category="Electronics", foreign_transaction=True,
             location_mismatch=True, device_trust_score=10, velocity_last_24h=8, cardholder_age=35)


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1) < 1e-9


def test_normal_transaction_is_low():
    r = aggregate(ScoreRequest(**NORMAL))
    assert r["tier"] == "Low" and r["score"] <= 30


def test_risky_transaction_scores_well_above_normal():
    risky, normal = aggregate(ScoreRequest(**RISKY)), aggregate(ScoreRequest(**NORMAL))
    assert risky["score"] >= 45 and risky["score"] > normal["score"] + 30


def test_response_has_drivers_key():
    assert "drivers" in aggregate(ScoreRequest(**RISKY))