def test_agent_create_get_and_list_contract(client):
    create_response = client.post(
        "/api/v1/agents",
        json={
            "name": "sales-agent",
            "description": "Analyze sales data",
            "status": "draft",
            "category": "sales",
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["code"] == 200
    assert created["message"] == "success"
    assert created["data"]["id"] == 1
    assert created["data"]["name"] == "sales-agent"

    get_response = client.get("/api/v1/agents/1")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["name"] == "sales-agent"

    list_response = client.get("/api/v1/agents")
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1


def test_http_error_uses_api_response_contract(client):
    response = client.get("/api/v1/agents/404")

    assert response.status_code == 404
    assert response.json() == {
        "code": 404,
        "message": "Agent not found",
        "data": None,
    }


def test_validation_error_uses_api_response_contract(client):
    response = client.post("/api/v1/agents", json={"description": "missing name"})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == 422
    assert body["message"] == "validation error"
    assert body["data"][0]["loc"][-1] == "name"


def test_datasource_contract(client):
    response = client.post(
        "/api/v1/datasources",
        json={
            "name": "local-mysql",
            "type": "mysql",
            "host": "localhost",
            "port": 3306,
            "database_name": "demo",
            "username": "root",
            "password": "secret",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "local-mysql"

    list_response = client.get("/api/v1/datasources")
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["test_status"] == "unknown"


def test_knowledge_contracts(client):
    agent_id = client.post("/api/v1/agents", json={"name": "knowledge-agent"}).json()["data"]["id"]

    business_response = client.post(
        f"/api/v1/agents/{agent_id}/business-knowledge",
        json={
            "agent_id": agent_id,
            "business_term": "GMV",
            "description": "Gross merchandise value",
        },
    )
    assert business_response.status_code == 200
    assert business_response.json()["data"]["business_term"] == "GMV"

    preset_response = client.post(
        "/api/v1/knowledge/preset-questions",
        json={
            "agent_id": agent_id,
            "question": "今日 GMV 是多少？",
            "is_active": 1,
        },
    )
    assert preset_response.status_code == 200

    list_response = client.get(f"/api/v1/knowledge/preset-questions/agent/{agent_id}")
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["question"] == "今日 GMV 是多少？"


def test_chat_session_and_message_contract(client):
    agent_id = client.post("/api/v1/agents", json={"name": "chat-agent"}).json()["data"]["id"]

    session_response = client.post(
        "/api/v1/chat/sessions",
        json={"agent_id": agent_id, "title": "hello"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["id"]

    message_response = client.post(
        "/api/v1/chat/messages",
        json={
            "session_id": session_id,
            "role": "user",
            "content": "show sales",
            "metadata": {"source": "test"},
        },
    )
    assert message_response.status_code == 200
    assert message_response.json()["data"]["metadata"] == {"source": "test"}

    list_response = client.get(f"/api/v1/chat/messages/session/{session_id}")
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["content"] == "show sales"


def test_agent_update_and_delete_contract(client):
    create_response = client.post("/api/v1/agents", json={"name": "update-agent"})
    assert create_response.status_code == 200
    agent_id = create_response.json()["data"]["id"]

    update_response = client.put(
        f"/api/v1/agents/{agent_id}",
        json={"name": "updated-agent", "api_key_enabled": 1},
    )
    assert update_response.status_code == 200
    updated = update_response.json()["data"]
    assert updated["name"] == "updated-agent"
    assert updated["api_key_enabled"] == 1

    delete_response = client.delete(f"/api/v1/agents/{agent_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Agent deleted successfully"

    get_response = client.get(f"/api/v1/agents/{agent_id}")
    assert get_response.status_code == 404


def test_datasource_get_update_delete_contract(client):
    create_response = client.post(
        "/api/v1/datasources",
        json={
            "name": "datasource-crud",
            "type": "mysql",
            "host": "localhost",
            "port": 3306,
            "database_name": "demo",
            "username": "root",
            "password": "secret",
        },
    )
    assert create_response.status_code == 200
    datasource_id = create_response.json()["data"]["id"]

    get_response = client.get(f"/api/v1/datasources/{datasource_id}")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["name"] == "datasource-crud"

    update_response = client.put(
        f"/api/v1/datasources/{datasource_id}",
        json={"name": "datasource-updated", "host": "127.0.0.1"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()["data"]
    assert updated["name"] == "datasource-updated"
    assert updated["host"] == "127.0.0.1"

    delete_response = client.delete(f"/api/v1/datasources/{datasource_id}")
    assert delete_response.status_code == 200
    assert "deleted successfully" in delete_response.json()["message"]

    get_response = client.get(f"/api/v1/datasources/{datasource_id}")
    assert get_response.status_code == 404


def test_agent_datasource_contract(client):
    agent_id = client.post("/api/v1/agents", json={"name": "linked-agent"}).json()["data"]["id"]
    datasource_id = client.post(
        "/api/v1/datasources",
        json={
            "name": "linked-datasource",
            "type": "mysql",
            "host": "localhost",
            "port": 3306,
            "database_name": "demo",
            "username": "root",
            "password": "secret",
        },
    ).json()["data"]["id"]

    link_response = client.post(
        "/api/v1/datasources/agent-datasources",
        json={"agent_id": agent_id, "datasource_id": datasource_id, "is_active": 1},
    )
    assert link_response.status_code == 200
    assert link_response.json()["data"]["is_active"] == 1

    list_response = client.get(f"/api/v1/datasources/agent-datasources/agent/{agent_id}")
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1
    assert list_response.json()["data"][0]["datasource_id"] == datasource_id


def test_logical_relation_contract(client):
    datasource_id = client.post(
        "/api/v1/datasources",
        json={
            "name": "relation-datasource",
            "type": "mysql",
            "host": "localhost",
            "port": 3306,
            "database_name": "demo",
            "username": "root",
            "password": "secret",
        },
    ).json()["data"]["id"]

    relation_response = client.post(
        "/api/v1/datasources/logical-relations",
        json={
            "datasource_id": datasource_id,
            "source_table_name": "orders",
            "source_column_name": "user_id",
            "target_table_name": "users",
            "target_column_name": "id",
            "relation_type": "N:1",
        },
    )
    assert relation_response.status_code == 200
    assert relation_response.json()["data"]["is_deleted"] == 0

    list_response = client.get(f"/api/v1/datasources/logical-relations/datasource/{datasource_id}")
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1
    assert list_response.json()["data"][0]["relation_type"] == "N:1"


def test_semantic_model_contract(client):
    agent_id = client.post("/api/v1/agents", json={"name": "semantic-agent"}).json()["data"]["id"]

    model_response = client.post(
        "/api/v1/knowledge/semantic-models",
        json={
            "agent_id": agent_id,
            "datasource_id": 1,
            "table_name": "orders",
            "column_name": "amount",
            "business_name": "订单金额",
            "data_type": "decimal",
            "status": 1,
        },
    )
    assert model_response.status_code == 200
    assert model_response.json()["data"]["business_name"] == "订单金额"
    assert model_response.json()["data"]["status"] == 1

    list_response = client.get(f"/api/v1/knowledge/semantic-models/agent/{agent_id}")
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1


def test_agent_knowledge_contract(client):
    agent_id = client.post("/api/v1/agents", json={"name": "knowledge-doc-agent"}).json()["data"][
        "id"
    ]

    knowledge_response = client.post(
        "/api/v1/knowledge/agent-knowledge",
        json={
            "agent_id": agent_id,
            "title": "退换货政策",
            "type": "DOCUMENT",
            "content": "支持7天无理由退货",
        },
    )
    assert knowledge_response.status_code == 200
    assert knowledge_response.json()["data"]["title"] == "退换货政策"

    list_response = client.get(f"/api/v1/knowledge/agent-knowledge/agent/{agent_id}")
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1
    assert list_response.json()["data"][0]["type"] == "DOCUMENT"


def test_chat_session_get_update_and_list_by_agent_contract(client):
    agent_id = client.post("/api/v1/agents", json={"name": "chat-session-agent"}).json()["data"][
        "id"
    ]

    session_response = client.post(
        "/api/v1/chat/sessions",
        json={"agent_id": agent_id, "title": "session-title"},
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["data"]["id"]

    get_response = client.get(f"/api/v1/chat/sessions/{session_id}")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["title"] == "session-title"

    update_response = client.put(
        f"/api/v1/chat/sessions/{session_id}",
        json={"title": "updated-title", "status": "archived"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["title"] == "updated-title"
    assert update_response.json()["data"]["status"] == "archived"

    list_response = client.get(f"/api/v1/chat/sessions/agent/{agent_id}")
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1
    assert list_response.json()["data"][0]["title"] == "updated-title"


def test_user_prompt_config_contract(client):
    agent_id = client.post("/api/v1/agents", json={"name": "prompt-agent"}).json()["data"]["id"]

    create_response = client.post(
        "/api/v1/chat/prompt-configs",
        json={
            "name": "sales-prompt",
            "prompt_type": "SALES",
            "system_prompt": "你是一个销售分析助手",
            "enabled": 1,
            "agent_id": agent_id,
        },
    )
    assert create_response.status_code == 200
    assert create_response.json()["data"]["name"] == "sales-prompt"

    list_response = client.get(
        "/api/v1/chat/prompt-configs", params={"prompt_type": "SALES", "agent_id": agent_id}
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1
    assert list_response.json()["data"][0]["system_prompt"] == "你是一个销售分析助手"


def test_model_config_contract(client):
    create_response = client.post(
        "/api/v1/chat/model-configs",
        json={
            "provider": "openai",
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-test",
            "model_name": "gpt-4o",
            "model_type": "CHAT",
            "is_active": 1,
        },
    )
    assert create_response.status_code == 200
    config_id = create_response.json()["data"]["id"]
    assert create_response.json()["data"]["is_active"] == 1

    list_response = client.get("/api/v1/chat/model-configs")
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1

    update_response = client.put(
        f"/api/v1/chat/model-configs/{config_id}",
        json={"model_name": "gpt-4o-mini"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["model_name"] == "gpt-4o-mini"
