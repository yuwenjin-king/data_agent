import os
import sqlite3
import tempfile

import pytest


@pytest.fixture()
def sqlite_datasource_file():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, amount REAL)")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    conn.close()
    yield path
    os.unlink(path)


def test_agent_publish_and_offline(client):
    create_response = client.post("/api/v1/agents", json={"name": "lifecycle-agent"})
    assert create_response.status_code == 200
    agent_id = create_response.json()["data"]["id"]
    assert create_response.json()["data"]["status"] == "draft"

    publish_response = client.post(f"/api/v1/agents/{agent_id}/publish")
    assert publish_response.status_code == 200
    assert publish_response.json()["data"]["status"] == "published"

    offline_response = client.post(f"/api/v1/agents/{agent_id}/offline")
    assert offline_response.status_code == 200
    assert offline_response.json()["data"]["status"] == "offline"


def test_agent_api_key_lifecycle(client):
    create_response = client.post("/api/v1/agents", json={"name": "key-agent"})
    agent_id = create_response.json()["data"]["id"]

    generate_response = client.post(f"/api/v1/agents/{agent_id}/api-key/generate")
    assert generate_response.status_code == 200
    data = generate_response.json()["data"]
    assert data["api_key"].startswith("sk-")
    assert data["api_key_enabled"] == 1

    get_response = client.get(f"/api/v1/agents/{agent_id}/api-key")
    assert get_response.status_code == 200
    masked = get_response.json()["data"]
    assert masked["masked_key"].startswith("****")
    assert masked["api_key_enabled"] == 1
    assert masked.get("api_key") is None

    disable_response = client.post(
        f"/api/v1/agents/{agent_id}/api-key/enable", params={"enabled": "false"}
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["data"]["api_key_enabled"] == 0

    enable_response = client.post(
        f"/api/v1/agents/{agent_id}/api-key/enable", params={"enabled": "true"}
    )
    assert enable_response.status_code == 200
    assert enable_response.json()["data"]["api_key_enabled"] == 1

    delete_response = client.delete(f"/api/v1/agents/{agent_id}/api-key")
    assert delete_response.status_code == 200

    get_after_delete = client.get(f"/api/v1/agents/{agent_id}/api-key")
    assert get_after_delete.status_code == 200
    assert get_after_delete.json()["data"]["masked_key"] is None
    assert get_after_delete.json()["data"]["api_key_enabled"] == 0


def test_datasource_types(client):
    response = client.get("/api/v1/datasources/types")
    assert response.status_code == 200
    types = response.json()["data"]
    assert len(types) >= 2
    assert any(t["type"] == "mysql" for t in types)
    assert any(t["type"] == "postgresql" for t in types)


def test_datasource_connection_test_with_sqlite(client, sqlite_datasource_file):
    create_response = client.post(
        "/api/v1/datasources",
        json={
            "name": "sqlite-test",
            "type": "sqlite",
            "host": "localhost",
            "port": 0,
            "database_name": sqlite_datasource_file,
            "username": "",
            "password": "",
        },
    )
    assert create_response.status_code == 200
    datasource_id = create_response.json()["data"]["id"]

    test_response = client.post(f"/api/v1/datasources/{datasource_id}/test")
    assert test_response.status_code == 200
    assert test_response.json()["data"]["success"] is True
    assert test_response.json()["data"]["message"] == "Connection successful"

    get_response = client.get(f"/api/v1/datasources/{datasource_id}")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["test_status"] == "success"


def test_datasource_tables_and_columns(client, sqlite_datasource_file):
    create_response = client.post(
        "/api/v1/datasources",
        json={
            "name": "sqlite-tables",
            "type": "sqlite",
            "host": "localhost",
            "port": 0,
            "database_name": sqlite_datasource_file,
            "username": "",
            "password": "",
        },
    )
    datasource_id = create_response.json()["data"]["id"]

    tables_response = client.get(f"/api/v1/datasources/{datasource_id}/tables")
    assert tables_response.status_code == 200
    tables = tables_response.json()["data"]
    assert "orders" in tables
    assert "users" in tables

    columns_response = client.get(f"/api/v1/datasources/{datasource_id}/tables/orders/columns")
    assert columns_response.status_code == 200
    columns = columns_response.json()["data"]
    assert "id" in columns
    assert "amount" in columns


def test_datasource_password_not_exposed_in_response(client):
    response = client.post(
        "/api/v1/datasources",
        json={
            "name": "secret-datasource",
            "type": "mysql",
            "host": "localhost",
            "port": 3306,
            "database_name": "demo",
            "username": "root",
            "password": "super-secret",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "password" not in data


def test_agent_schema_init(client, db_session, sqlite_datasource_file):
    agent_id = client.post("/api/v1/agents", json={"name": "schema-agent"}).json()["data"]["id"]
    datasource_id = client.post(
        "/api/v1/datasources",
        json={
            "name": "sqlite-schema",
            "type": "sqlite",
            "host": "localhost",
            "port": 0,
            "database_name": sqlite_datasource_file,
            "username": "",
            "password": "",
        },
    ).json()["data"]["id"]

    link_response = client.post(
        "/api/v1/datasources/agent-datasources",
        json={"agent_id": agent_id, "datasource_id": datasource_id, "is_active": 1},
    )
    assert link_response.status_code == 200

    init_response = client.post(
        f"/api/v1/agents/{agent_id}/datasources/init-schema",
        json={"table_names": ["orders", "users"]},
    )
    assert init_response.status_code == 200
    assert init_response.json()["data"] == ["orders", "users"]

    list_response = client.get(f"/api/v1/datasources/agent-datasources/agent/{agent_id}")
    assert list_response.status_code == 200
    link = list_response.json()["data"][0]
    assert link["datasource_id"] == datasource_id

    # Verify AgentDatasourceTables rows via the test ORM session
    from app.models.datasource import AgentDatasourceTables

    agent_datasource_id = link["id"]
    tables = (
        db_session.query(AgentDatasourceTables)
        .filter(AgentDatasourceTables.agent_datasource_id == agent_datasource_id)
        .all()
    )
    table_names = {t.table_name for t in tables}
    assert table_names == {"orders", "users"}
