import pytest

from detection import ml
from detection.explain import drivers
from schemas import ScoreRequest

pytestmark = pytest.mark.skipif(ml.load() is None, reason="run ml/train.py first")

REQ = dict(amount=900, transaction_hour=3, merchant_category="Electronics", foreign_transaction=True,
           location_mismatch=True, device_trust_score=20, velocity_last_24h=6, cardholder_age=35)


def test_ml_score_is_in_range():
    assert 0 <= ml.ml_score(ScoreRequest(**REQ), {}) <= 100


def test_drivers_cover_every_feature():
    d = drivers(ScoreRequest(**REQ))
    assert {x["feature"] for x in d} == {"Amount", "Hour of day", "Foreign transaction", "Location mismatch",
                                         "Device trust", "Velocity (24h)", "Cardholder age", "Merchant category"}
    assert 90 <= sum(abs(x["impact"]) for x in d) <= 110