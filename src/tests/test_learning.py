import shutil

import pytest
from fastapi.testclient import TestClient

import db
import main
from detection import ml
from detection import retrain as rt

client = TestClient(main.app)
PAY = dict(amount=900, transaction_hour=3, merchant_category="Electronics", foreign_transaction=True,
           location_mismatch=True, device_trust_score=10, velocity_last_24h=8, cardholder_age=35)
CUSTOMER = {"x-role": "customer", "x-user": "Test User"}
ANALYST, ADMIN = {"x-role": "analyst"}, {"x-role": "admin"}


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB", tmp_path / "t.db")
    db.init()


def force_tier(monkeypatch, tier):
    monkeypatch.setattr(main, "aggregate", lambda req: {"score": 90, "probability": 95, "tier": tier, "action": "x",
                                                        "parts": [{"label": "Rules", "points": 20.0}], "drivers": []})


def test_risky_payment_opens_a_case(monkeypatch):
    force_tier(monkeypatch, "Critical")
    r = client.post("/transactions", json=PAY, headers=CUSTOMER).json()
    assert r["status"] == "blocked" and r["case_id"]
    assert r["case_id"] in [c["id"] for c in client.get("/cases", headers=ANALYST).json()]


def test_low_risk_payment_opens_no_case(monkeypatch):
    force_tier(monkeypatch, "Low")
    r = client.post("/transactions", json=PAY, headers=CUSTOMER).json()
    assert r["status"] == "approved" and r["case_id"] is None


@pytest.mark.parametrize("decision,label", [("Confirmed fraud", 1), ("False positive", 0)])
def test_analyst_decision_labels_the_stored_record(monkeypatch, decision, label):
    force_tier(monkeypatch, "Critical")
    case = client.post("/transactions", json=PAY, headers=CUSTOMER).json()["case_id"]
    client.post("/decision", json={"case_id": case, "decision": decision}, headers=ANALYST)
    rec = db.labelled_records()
    assert len(rec) == 1 and rec[0][1] == label and rec[0][0]["amount"] == 900


def test_escalation_leaves_the_record_unlabelled(monkeypatch):
    force_tier(monkeypatch, "Critical")
    case = client.post("/transactions", json=PAY, headers=CUSTOMER).json()["case_id"]
    client.post("/decision", json={"case_id": case, "decision": "Escalated"}, headers=ANALYST)
    assert db.labelled_records() == [] and db.model_stats()["unlabelled"] == 1


def test_role_limits():
    assert client.post("/transactions", json=PAY, headers=ANALYST).status_code == 403
    assert client.post("/retrain", headers=ANALYST).status_code == 403
    assert client.get("/model", headers=CUSTOMER).status_code == 403


def test_retrain_refuses_without_enough_labels():
    r = client.post("/retrain", headers=ADMIN)
    assert r.status_code == 200 and r.json()["promoted"] is False
    assert len(client.get("/model", headers=ADMIN).json()["versions"]) == 1


@pytest.mark.skipif(ml.load() is None or not rt.BASE_CSV.exists(), reason="needs trained models and ml/data CSV")
def test_retrain_end_to_end(tmp_path, monkeypatch):
    shutil.copytree(ml.ART, tmp_path / "art")  # never touch the real artifacts from a test
    monkeypatch.setattr(ml, "ART", tmp_path / "art")
    ml.load.cache_clear(); ml.meta.cache_clear()
    try:
        assert client.post("/demo/new-pattern", headers=ADMIN).json()["added"] > 0
        res = client.post("/retrain", headers=ADMIN).json()
        assert {"champion_pr_auc", "challenger_pr_auc", "promoted"} <= set(res)
    finally:
        monkeypatch.undo()
        ml.load.cache_clear(); ml.meta.cache_clear()
