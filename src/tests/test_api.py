PAYLOAD = dict(amount=500, transaction_hour=14, merchant_category="Grocery", foreign_transaction=False,
               location_mismatch=False, device_trust_score=70, velocity_last_24h=1, cardholder_age=40)


def test_score_needs_login(client):
    assert client.post("/score", json=PAYLOAD).status_code == 401


def test_staff_can_score_customer_cannot(client, as_):
    assert client.post("/score", json=PAYLOAD, headers=as_("analyst")).status_code == 200
    assert client.post("/score", json=PAYLOAD, headers=as_("customer")).status_code == 403


def test_customer_cannot_see_cases(client, as_):
    assert client.get("/cases", headers=as_("customer")).status_code == 403


def test_only_analyst_can_decide(client, as_):
    body = {"case_id": "FG-10432", "decision": "Confirmed fraud"}
    assert client.post("/decision", json=body, headers=as_("admin")).status_code == 403
    assert client.post("/decision", json=body, headers=as_("analyst")).status_code == 200
    assert client.post("/decision", json=body, headers=as_("analyst")).status_code == 409


def test_decision_lands_in_audit_log(client, as_):
    client.post("/decision", json={"case_id": "FG-10431", "decision": "False positive"}, headers=as_("analyst"))
    log = client.get("/audit", headers=as_("admin")).json()
    assert log[0]["case_id"] == "FG-10431" and log[0]["by_role"] == "analyst"


def test_customer_sees_only_own_cases(client, as_):
    r = client.get("/my-cases", headers=as_("customer"))
    assert r.status_code == 200 and {c["owner"] for c in r.json()} == {"R. Mehta"}
    assert client.get("/my-cases", headers=as_("analyst")).status_code == 403


def test_meta_lists_categories_for_any_signed_in_user(client, as_):
    assert len(client.get("/meta", headers=as_("analyst")).json()["categories"]) > 0
    assert client.get("/meta", headers=as_("customer")).status_code == 200
    assert client.get("/meta").status_code == 401