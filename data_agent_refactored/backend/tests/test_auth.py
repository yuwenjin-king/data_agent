"""Tests for the toggleable JWT auth (AUTH_ENABLED on/off)."""

from app.core.config import settings
from app.core.security import hash_password
from app.models.agent import Agent
from app.models.user import User
from app.services.agent_service import agent_crud


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


def test_completions_blocks_without_credentials_when_enabled(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    resp = client.post(
        "/api/v1/chat/completions", json={"agent_id": 1, "message": "hi", "stream": False}
    )
    assert resp.status_code == 401


def test_completions_accepts_login_token_when_enabled(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    _make_user(db_session)
    login = client.post("/api/v1/auth/login", data={"username": "testadmin", "password": "secret"})
    token = login.json()["access_token"]

    resp = client.post(
        "/api/v1/chat/completions",
        json={"agent_id": 1, "message": "hi", "stream": False},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200


def test_completions_accepts_bound_agent_api_key_when_enabled(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    agent = Agent(name="Sales Agent", status="published")
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    _, raw_key = agent_crud.generate_api_key(db_session, agent_id=agent.id)

    resp = client.post(
        "/api/v1/chat/completions",
        json={"agent_id": agent.id, "message": "hi", "stream": False},
        headers={"X-Agent-API-Key": raw_key},
    )

    assert resp.status_code == 200


def test_completions_rejects_unbound_agent_api_key_when_enabled(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    first = Agent(name="First Agent", status="published")
    second = Agent(name="Second Agent", status="published")
    db_session.add_all([first, second])
    db_session.commit()
    db_session.refresh(first)
    db_session.refresh(second)
    _, raw_key = agent_crud.generate_api_key(db_session, agent_id=first.id)

    resp = client.post(
        "/api/v1/chat/completions",
        json={"agent_id": second.id, "message": "hi", "stream": False},
        headers={"X-Agent-API-Key": raw_key},
    )

    assert resp.status_code == 403
