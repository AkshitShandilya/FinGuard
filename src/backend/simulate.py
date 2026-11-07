"""Demo helper: labelled records that follow a fraud pattern the training data does not contain."""
import numpy as np

from detection import ml


def new_pattern(n: int = 60):
    m = ml.meta()
    rng, cats, p95 = np.random.default_rng(), m["categories"], m["amount_p95"]
    target = "Clothing" if "Clothing" in cats else cats[0]
    out = []
    for i in range(n):
        if i % 2 == 0:  # fraud that looks ordinary: domestic, trusted-ish device, daytime, one category
            f = dict(amount=round(float(rng.uniform(0.8, 1.6) * p95), 2), transaction_hour=int(rng.integers(10, 17)),
                     merchant_category=target, foreign_transaction=False, location_mismatch=False,
                     device_trust_score=int(rng.integers(55, 81)), velocity_last_24h=int(rng.integers(2, 5)),
                     cardholder_age=int(rng.integers(25, 61)))
        else:
            f = dict(amount=round(float(rng.lognormal(np.log(p95 / 4), 0.7)), 2), transaction_hour=int(rng.integers(7, 23)),
                     merchant_category=str(rng.choice(cats)), foreign_transaction=bool(rng.random() < 0.05),
                     location_mismatch=bool(rng.random() < 0.08), device_trust_score=int(np.clip(rng.normal(70, 12), 0, 100)),
                     velocity_last_24h=int(rng.poisson(1.2)), cardholder_age=int(rng.integers(25, 61)))
        out.append((f, int(i % 2 == 0)))
    return out
