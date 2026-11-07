"""Incremental learning. Analyst-labelled production records are folded back into the models.
Champion/challenger: the retrained model replaces the live one only if it holds up on a clean holdout."""
import shutil
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from . import ml

BASE_CSV = Path(__file__).resolve().parents[2] / "ml" / "data" / "creditcard_fraud.csv"
MIN_LABELS, MIN_FRAUDS = 20, 5  # enough that the new-data holdout contains real fraud
NEW_WEIGHT = 5.0   # a production label counts 5x a base row, so a small batch can actually move the model
TOLERANCE = 0.05   # max drop allowed on the clean holdout (it has ~30 fraud rows, so smaller gaps are noise)
PARAMS = dict(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
              min_child_weight=2, eval_metric="aucpr")  # same as ml/train.py


def _encode(frame, m):
    X = frame[m["numeric"]].astype(float).copy()
    for c in m["categories"]:
        X[f"cat_{c}"] = (frame["merchant_category"].astype(str) == c).astype(float)
    return X


def _base(m):
    """Same cleaning and split as ml/train.py, so the holdout is the same clean data every time."""
    df = pd.read_csv(BASE_CSV)
    df = df.dropna(subset=m["numeric"] + ["merchant_category", "is_fraud"]).drop(columns=["transaction_id"], errors="ignore").reset_index(drop=True)
    X, y = _encode(df, m), df["is_fraud"].astype(int).values
    return train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)


def retrain(labelled, everything) -> dict:
    stamp = datetime.now().isoformat(timespec="seconds")
    n, frauds = len(labelled), int(sum(lab for _, lab in labelled))
    base = {"trained_at": stamp, "new_labels": n, "new_frauds": frauds}
    cur = ml.load()
    if cur is None or not BASE_CSV.exists():
        return {**base, "promoted": False, "reason": "Run ml/train.py first and keep the dataset in ml/data/."}
    if n < MIN_LABELS or frauds < MIN_FRAUDS:
        return {**base, "promoted": False,
                "reason": f"Need at least {MIN_LABELS} labelled records with {MIN_FRAUDS}+ confirmed frauds (have {n} and {frauds})."}

    m = ml.meta()
    Xtr, Xte, ytr, yte = _base(m)
    champ = float(average_precision_score(yte, cur[0].predict_proba(Xte.values)[:, 1]))

    Xnew = _encode(pd.DataFrame([f for f, _ in labelled]), m).values
    ynew = np.array([lab for _, lab in labelled])
    Xn_tr, Xn_te, yn_tr, yn_te = train_test_split(Xnew, ynew, test_size=0.3, stratify=ynew, random_state=42)

    def fit(Xn, yn):
        X, y = np.vstack([Xtr.values, Xn]), np.concatenate([ytr, yn])
        w = np.concatenate([np.ones(len(ytr)), np.full(len(yn), NEW_WEIGHT)])
        return XGBClassifier(**PARAMS).fit(X, y, sample_weight=w)

    def ap(model, X, y):
        return float(average_precision_score(y, model.predict_proba(X)[:, 1]))

    cand = fit(Xn_tr, yn_tr)  # judged on records it has never seen, old and new
    champ_old, chall_old = ap(cur[0], Xte.values, yte), ap(cand, Xte.values, yte)
    champ_new, chall_new = ap(cur[0], Xn_te, yn_te), ap(cand, Xn_te, yn_te)
    r = lambda v: round(v, 4)
    out = {**base, "champion_pr_auc": r(champ_old), "challenger_pr_auc": r(chall_old),
           "new_data_champion_pr_auc": r(champ_new), "new_data_challenger_pr_auc": r(chall_new)}
    detail = f"Original holdout {r(champ_old)} -> {r(chall_old)}. Held-out new records {r(champ_new)} -> {r(chall_new)}."
    if chall_old < champ_old - TOLERANCE:
        return {**out, "promoted": False, "reason": f"It forgot too much of the original data, so the live model was kept. {detail}"}
    if chall_new <= champ_new:
        return {**out, "promoted": False, "reason": f"It did not improve on the new records, so the live model was kept. {detail}"}
    xgb = fit(Xnew, ynew)  # checks passed: refit on every new label

    # Isolation Forest is unsupervised, so it learns from every transaction seen, labelled or not.
    seen = _encode(pd.DataFrame(everything), m).values if everything else np.empty((0, Xtr.shape[1]))
    Xi = np.vstack([Xtr.values, seen])
    iso = IsolationForest(n_estimators=200, contamination=float(ytr.mean()), random_state=42).fit(Xi)
    s = iso.score_samples(Xi)
    iso_art = {"model": iso, "lo": float(np.percentile(s, 1)), "hi": float(np.percentile(s, 99))}

    archive = ml.ART / "archive" / stamp.replace(":", "-")
    archive.mkdir(parents=True, exist_ok=True)
    for name in ("xgb.joblib", "iso.joblib"):
        shutil.copy2(ml.ART / name, archive / name)  # the previous version stays recoverable
    joblib.dump(xgb, ml.ART / "xgb.joblib")
    joblib.dump(iso_art, ml.ART / "iso.joblib")
    ml.load.cache_clear()
    ml.meta.cache_clear()
    return {**out, "promoted": True, "reason": f"Promoted. {detail} Previous version archived."}