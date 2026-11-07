import pytest
from fastapi.testclient import TestClient

import db
from main import app

client = TestClient(app)
PAYLOAD = dict(amount=500, transaction_hour=14, merchant_category="Grocery", foreign_transaction=False,
               location_mismatch=False, device_trust_score=70, velocity_last_24h=1, cardholder_age=40)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB", tmp_path / "t.db")
    db.init()


def test_score_needs_a_role():
    assert client.post("/score", json=PAYLOAD).status_code == 403


def test_customer_cannot_see_cases():
    assert client.get("/cases", headers={"x-role": "customer"}).status_code == 403


def test_only_analyst_can_decide():
    body = {"case_id": "FG-10432", "decision": "Confirmed fraud"}
    assert client.post("/decision", json=body, headers={"x-role": "admin"}).status_code == 403
    assert client.post("/decision", json=body, headers={"x-role": "analyst"}).status_code == 200
    assert client.post("/decision", json=body, headers={"x-role": "analyst"}).status_code == 409


def test_decision_lands_in_audit_log():
    body = {"case_id": "FG-10431", "decision": "False positive"}
    client.post("/decision", json=body, headers={"x-role": "analyst"})
    log = client.get("/audit", headers={"x-role": "admin"}).json()
    assert log[0]["case_id"] == "FG-10431" and log[0]["by_role"] == "analyst"


def test_customer_sees_only_own_cases():
    r = client.get("/my-cases", headers={"x-role": "customer", "x-user": "R. Mehta"})
    assert r.status_code == 200 and {c["owner"] for c in r.json()} == {"R. Mehta"}
    assert client.get("/my-cases", headers={"x-role": "analyst", "x-user": "R. Mehta"}).status_code == 403


def test_meta_lists_categories():
    ok = client.get("/meta", headers={"x-role": "analyst"})
    assert ok.status_code == 200 and len(ok.json()["categories"]) > 0
    assert client.get("/meta", headers={"x-role": "customer"}).status_code == 200
    assert client.get("/meta").status_code == 403