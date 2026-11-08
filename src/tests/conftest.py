import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import pytest
from fastapi.testclient import TestClient

import auth
import db

USERS = {"customer": "r.mehta", "analyst": "analyst", "risk": "risk", "admin": "admin"}


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB", tmp_path / "t.db")
    db.init()
    auth.FAILS.clear()


@pytest.fixture
def client():
    import main
    return TestClient(main.app)


@pytest.fixture
def as_(client):
    """as_('analyst') -> headers carrying a real login token for that role."""
    def headers(role):
        r = client.post("/auth/login", json={"username": USERS[role], "password": auth.DEMO_PASSWORD})
        return {"Authorization": f"Bearer {r.json()['token']}"}
    return headers