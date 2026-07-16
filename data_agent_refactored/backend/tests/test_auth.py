"""Tests for the toggleable JWT auth (AUTH_ENABLED on/off)."""

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User


def _make_user(db_session, username="testadmin", password="secret"):
    db_session.add(
        User(
            username=username,
            hashed_password=hash_password(password),
            is_active=1,
            is_superuser=1,
        )
    )
    db_session.commit()
    return username, password


def test_auth_status_reports_disabled_by_default(client):
    resp = client.get("/api/v1/auth/status")
    assert resp.status_code == 200
    assert resp.json()["data"]["auth_enabled"] is False


def test_management_routes_open_when_auth_disabled(client):
    # AUTH_ENABLED off → require_auth is a no-op; no token needed.
    assert client.get("/api/v1/agents").status_code == 200


def test_management_route_blocks_without_token_when_enabled(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    assert client.get("/api/v1/agents").status_code == 401


def test_login_and_authenticated_access(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    _make_user(db_session)

    # No token → 401.
    assert client.get("/api/v1/agents").status_code == 401

    login = client.post("/api/v1/auth/login", data={"username": "testadmin", "password": "secret"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    # Token grants access to protected management routes.
    resp = client.get("/api/v1/agents", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["data"]["username"] == "testadmin"


def test_login_rejects_wrong_password(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    _make_user(db_session)
    resp = client.post("/api/v1/auth/login", data={"username": "testadmin", "password": "wrong"})
    assert resp.status_code == 401


def test_completions_stays_open_when_enabled(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    # /completions lives on the open router (agent-facing) — must not 401.
    resp = client.post(
        "/api/v1/chat/completions", json={"agent_id": 1, "message": "hi", "stream": False}
    )
    assert resp.status_code != 401
