"""Trains FinGuard's models on the credit-card fraud CSV and saves them to ml/artifacts/.

    python src/ml/train.py                      # uses src/ml/data/creditcard_fraud.csv
    python src/ml/train.py path/to/file.csv     # or point at another file

The dataset is synthetic. Say so in the report: the metrics describe this dataset only."""
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, precision_recall_curve, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score, train_test_split
from xgboost import XGBClassifier

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))
from detection.rules import FLAG_AT, rule_score  # noqa: E402  same rules the API uses, for the baseline

CSV = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "data" / "creditcard_fraud.csv"
NUMERIC = ["amount", "transaction_hour", "foreign_transaction", "location_mismatch",
           "device_trust_score", "velocity_last_24h", "cardholder_age"]
REQUIRED = NUMERIC + ["merchant_category", "is_fraud"]

if not CSV.exists():
    sys.exit(f"Dataset not found: {CSV}\nPut the CSV at src/ml/data/creditcard_fraud.csv")
df = pd.read_csv(CSV)
missing = [c for c in REQUIRED if c not in df.columns]
if missing:
    sys.exit(f"CSV is missing columns: {missing}\nFound: {list(df.columns)}")
df = df.dropna(subset=REQUIRED).drop(columns=["transaction_id"], errors="ignore").reset_index(drop=True)

categories = sorted(df["merchant_category"].astype(str).unique())
y = df["is_fraud"].astype(int).values
print(f"rows={len(df)}  fraud={y.sum()} ({y.mean():.2%})  categories={categories}")


def encode(d):
    X = d[NUMERIC].astype(float).copy()
    for c in categories:
        X[f"cat_{c}"] = (d["merchant_category"].astype(str) == c).astype(float)
    return X


X = encode(df)

# Leakage check: a single feature that separates fraud almost perfectly is a shortcut, not a pattern.
single = {c: round(float(max(a, 1 - a)), 3) for c in NUMERIC for a in [roc_auc_score(y, df[c])]}
leaky = [c for c, a in single.items() if a > 0.95]
if leaky:
    print(f"WARNING: single-feature AUC above 0.95 for {leaky}. The model may be learning a shortcut.")

Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
params = dict(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
              min_child_weight=2, eval_metric="aucpr")
skf = StratifiedKFold(5, shuffle=True, random_state=42)
cv = cross_val_score(XGBClassifier(**params), Xtr.values, ytr, cv=skf, scoring="average_precision")

# Threshold from out-of-fold predictions (stable with few fraud rows), never from the test set.
oof = cross_val_predict(XGBClassifier(**params), Xtr.values, ytr, cv=skf, method="predict_proba")[:, 1]
pr, rc, th = precision_recall_curve(ytr, oof)
f2 = 5 * pr[:-1] * rc[:-1] / np.maximum(4 * pr[:-1] + rc[:-1], 1e-9)  # recall counts double
thr = float(th[f2.argmax()])

xgb = XGBClassifier(**params).fit(Xtr.values, ytr)
p = xgb.predict_proba(Xte.values)[:, 1]
pred = (p >= thr).astype(int)

iso = IsolationForest(n_estimators=200, contamination=float(y.mean()), random_state=42).fit(Xtr.values)
s_tr = iso.score_samples(Xtr.values)
iso_art = {"model": iso, "lo": float(np.percentile(s_tr, 1)), "hi": float(np.percentile(s_tr, 99))}

p95 = float(np.percentile(df["amount"], 95))
test_rows = df.loc[Xte.index].to_dict("records")
base = np.array([int(rule_score(SimpleNamespace(**r), p95) >= FLAG_AT) for r in test_rows])

r4 = lambda v: round(float(v), 4)
metrics = {
    "note": "Synthetic dataset. Metrics describe this dataset, not real-world performance.",
    "rows": len(df), "fraud_rows": int(y.sum()), "fraud_rate": r4(y.mean()),
    "test_rows": len(yte), "test_fraud_rows": int(yte.sum()),
    "xgboost": {"threshold_from_cv": round(thr, 3), "pr_auc": r4(average_precision_score(yte, p)),
                "roc_auc": r4(roc_auc_score(yte, p)), "precision": r4(precision_score(yte, pred, zero_division=0)),
                "recall": r4(recall_score(yte, pred)), "cv_pr_auc_mean": r4(cv.mean()), "cv_pr_auc_std": r4(cv.std())},
    "rules_only_baseline": {"precision": r4(precision_score(yte, base, zero_division=0)), "recall": r4(recall_score(yte, base))},
    "isolation_forest_unsupervised_roc_auc": r4(roc_auc_score(yte, -iso.score_samples(Xte.values))),
    "single_feature_auc": single,
}

# ---------------------------------------------------------------------------------------------
# Stress test: how fast do the scores fall when the data gets messy? Each level is repeated with
# 5 random seeds and reported as mean +/- std. A model that degrades gradually is more believable
# than one that is perfect on clean data only.
# ---------------------------------------------------------------------------------------------
LEVELS, SEEDS = [0.0, 0.1, 0.2, 0.3, 0.5], range(5)
Xte_rows = df.loc[Xte.index]


def score(model, X, yt):
    pr = model.predict_proba(X)[:, 1]
    return average_precision_score(yt, pr), roc_auc_score(yt, pr)


def summarize(vals):
    a = np.array(vals)
    return {"pr_auc": r4(a[:, 0].mean()), "pr_auc_std": r4(a[:, 0].std()),
            "roc_auc": r4(a[:, 1].mean()), "roc_auc_std": r4(a[:, 1].std())}


def noisy_labels(labels, q, rs):
    """Hide a share q of the fraud labels (unreported fraud) and add the same number of false alarms."""
    out = labels.copy()
    pos, neg = np.where(labels == 1)[0], np.where(labels == 0)[0]
    k = int(round(q * len(pos)))
    out[rs.choice(pos, k, replace=False)] = 0
    out[rs.choice(neg, k, replace=False)] = 1
    return out


def perturb(d, k, rs):
    """Blur the test transactions: noisy amounts, shifted hours, flipped flags, jittered trust and velocity."""
    d, n = d.copy(), len(d)
    d["amount"] = d["amount"] * np.exp(rs.normal(0, k, n))
    d["transaction_hour"] = (d["transaction_hour"] + np.round(rs.normal(0, 8 * k, n))).astype(int) % 24
    for c in ["foreign_transaction", "location_mismatch"]:
        d[c] = np.where(rs.random(n) < k / 4, 1 - d[c], d[c])
    d["device_trust_score"] = np.clip(d["device_trust_score"] + rs.normal(0, 40 * k, n), 0, 100)
    d["velocity_last_24h"] = np.clip(d["velocity_last_24h"] + np.round(rs.normal(0, 4 * k, n)), 0, None)
    return encode(d).values


label_noise, feature_noise = {}, {}
for q in LEVELS:
    runs = []
    for sd in SEEDS:
        m = XGBClassifier(**params, random_state=sd).fit(Xtr.values, noisy_labels(ytr, q, np.random.default_rng(sd)))
        runs.append(score(m, Xte.values, yte))  # always scored against the CLEAN test labels
    label_noise[str(q)] = summarize(runs)
    runs = [score(xgb, perturb(Xte_rows, q, np.random.default_rng(sd)), yte) for sd in SEEDS]
    feature_noise[str(q)] = summarize(runs)

metrics_stress = {
    "label_noise": label_noise, "feature_noise": feature_noise,
    "how_to_read": "label_noise: share of training fraud labels hidden, plus the same number of false alarms; "
                   "scored on clean test labels. feature_noise: clean-trained model scored on blurred test "
                   "transactions. 0.0 = no noise.",
}
print("\nSTRESS TEST (PR-AUC, mean over 5 seeds)")
print(f"{'level':>6} | {'label noise':>12} | {'feature noise':>13}")
for q in LEVELS:
    print(f"{q:>6} | {label_noise[str(q)]['pr_auc']:>12} | {feature_noise[str(q)]['pr_auc']:>13}")
metrics["stress_test"] = metrics_stress

meta = {"numeric": NUMERIC, "categories": categories, "amount_p95": round(p95, 2),
        "amount_max": float(math.ceil(df["amount"].max()))}
(HERE / "artifacts").mkdir(exist_ok=True)
joblib.dump(xgb, HERE / "artifacts" / "xgb.joblib")
joblib.dump(iso_art, HERE / "artifacts" / "iso.joblib")
(HERE / "artifacts" / "meta.json").write_text(json.dumps(meta, indent=2))
(HERE / "artifacts" / "metrics.json").write_text(json.dumps(metrics, indent=2))
print(json.dumps(metrics, indent=2))