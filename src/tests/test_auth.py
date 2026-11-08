import time

import jwt

import auth
import db


def login(client, username="admin", password=None):
    return client.post("/auth/login", json={"username": username, "password": password or auth.DEMO_PASSWORD})


def test_login_returns_token_and_role(client):
    r = login(client, "analyst")
    assert r.status_code == 200 and r.json()["role"] == "analyst" and r.json()["token"]


def test_wrong_password_and_unknown_user_are_rejected(client):
    assert login(client, "admin", "nope").status_code == 401
    assert login(client, "ghost").status_code == 401


def test_me_returns_identity(client, as_):
    assert client.get("/auth/me", headers=as_("risk")).json()["role"] == "risk"


def test_a_role_header_no_longer_grants_anything(client):
    assert client.get("/cases", headers={"x-role": "admin"}).status_code == 401


def test_tampered_token_is_rejected(client, as_):
    token = as_("admin")["Authorization"] + "x"
    assert client.get("/auth/me", headers={"Authorization": token}).status_code == 401


def test_expired_token_is_rejected(client):
    old = jwt.encode({"sub": "admin", "exp": int(time.time()) - 10}, auth.SECRET, algorithm="HS256")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {old}"}).status_code == 401


def test_token_signed_with_another_key_is_rejected(client):
    forged = jwt.encode({"sub": "admin", "exp": int(time.time()) + 600}, "not-the-secret", algorithm="HS256")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_login_is_rate_limited(client):
    for _ in range(5):
        assert login(client, "admin", "bad").status_code == 401
    assert login(client, "admin", "bad").status_code == 429
    assert login(client).status_code == 429  # even the right password waits out the window


def test_passwords_are_stored_hashed():
    u = db.get_user("admin")
    assert u["pw_hash"] != auth.DEMO_PASSWORD and len(u["pw_hash"]) == 64 and u["salt"]
