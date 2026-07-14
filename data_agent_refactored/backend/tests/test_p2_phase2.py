import io
import os
import tempfile
from pathlib import Path

import openpyxl
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


@pytest.fixture()
def upload_dir(tmp_path):
    original = settings.UPLOAD_DIR
    new_dir = tmp_path / "uploads"
    new_dir.mkdir(parents=True, exist_ok=True)
    settings.UPLOAD_DIR = str(new_dir)
    yield new_dir
    settings.UPLOAD_DIR = original


def _make_excel_bytes(rows: list) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(
        ["表名*", "字段名*", "业务名称*", "数据类型*", "同义词", "业务描述", "字段注释", "创建时间"]
    )
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


def test_semantic_model_create_resolves_active_datasource(client, db_session):
    agent_id = client.post("/api/v1/agents", json={"name": "sm-agent"}).json()["data"]["id"]
    datasource_id = client.post(
        "/api/v1/datasources",
        json={
            "name": "sm-datasource",
            "type": "sqlite",
            "host": "localhost",
            "port": 0,
            "database_name": ":memory:",
            "username": "",
            "password": "",
        },
    ).json()["data"]["id"]
    client.post(
        "/api/v1/datasources/agent-datasources",
        json={"agent_id": agent_id, "datasource_id": datasource_id, "is_active": 1},
    )

    response = client.post(
        "/api/v1/knowledge/semantic-models",
        json={
            "agent_id": agent_id,
            "table_name": "orders",
            "column_name": "amount",
            "business_name": "订单金额",
            "data_type": "decimal",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["datasource_id"] == datasource_id
    assert data["status"] == 1


def test_semantic_model_get_update_delete(client, db_session):
    agent_id = client.post("/api/v1/agents", json={"name": "sm-crud-agent"}).json()["data"]["id"]
    datasource_id = client.post(
        "/api/v1/datasources",
        json={
            "name": "sm-crud-datasource",
            "type": "sqlite",
            "host": "localhost",
            "port": 0,
            "database_name": ":memory:",
            "username": "",
            "password": "",
        },
    ).json()["data"]["id"]

    create_response = client.post(
        "/api/v1/knowledge/semantic-models",
        json={
            "agent_id": agent_id,
            "datasource_id": datasource_id,
            "table_name": "users",
            "column_name": "id",
            "business_name": "用户ID",
            "data_type": "bigint",
        },
    )
    model_id = create_response.json()["data"]["id"]

    get_response = client.get(f"/api/v1/knowledge/semantic-models/{model_id}")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["business_name"] == "用户ID"

    update_response = client.put(
        f"/api/v1/knowledge/semantic-models/{model_id}",
        json={"business_name": "用户编号"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["business_name"] == "用户编号"

    delete_response = client.delete(f"/api/v1/knowledge/semantic-models/{model_id}")
    assert delete_response.status_code == 200

    get_after_delete = client.get(f"/api/v1/knowledge/semantic-models/{model_id}")
    assert get_after_delete.status_code == 404


def test_semantic_model_batch_delete(client, db_session):
    agent_id = client.post("/api/v1/agents", json={"name": "sm-batch-agent"}).json()["data"]["id"]
    datasource_id = client.post(
        "/api/v1/datasources",
        json={
            "name": "sm-batch-datasource",
            "type": "sqlite",
            "host": "localhost",
            "port": 0,
            "database_name": ":memory:",
            "username": "",
            "password": "",
        },
    ).json()["data"]["id"]

    ids = []
    for i in range(3):
        response = client.post(
            "/api/v1/knowledge/semantic-models",
            json={
                "agent_id": agent_id,
                "datasource_id": datasource_id,
                "table_name": f"t{i}",
                "column_name": f"c{i}",
                "business_name": f"b{i}",
                "data_type": "int",
            },
        )
        ids.append(response.json()["data"]["id"])

    import json as _json

    delete_response = client.request(
        "DELETE",
        "/api/v1/knowledge/semantic-models/batch",
        json={"ids": ids[:2]},
    )
    assert delete_response.status_code == 200

    list_response = client.get("/api/v1/knowledge/semantic-models", params={"agent_id": agent_id})
    assert len(list_response.json()["data"]) == 1


def test_semantic_model_enable_disable(client, db_session):
    agent_id = client.post("/api/v1/agents", json={"name": "sm-toggle-agent"}).json()["data"]["id"]
    datasource_id = client.post(
        "/api/v1/datasources",
        json={
            "name": "sm-toggle-datasource",
            "type": "sqlite",
            "host": "localhost",
            "port": 0,
            "database_name": ":memory:",
            "username": "",
            "password": "",
        },
    ).json()["data"]["id"]

    model_id = client.post(
        "/api/v1/knowledge/semantic-models",
        json={
            "agent_id": agent_id,
            "datasource_id": datasource_id,
            "table_name": "orders",
            "column_name": "amount",
            "business_name": "订单金额",
            "data_type": "decimal",
        },
    ).json()["data"]["id"]

    disable_response = client.put(f"/api/v1/knowledge/semantic-models/{model_id}/disable")
    assert disable_response.status_code == 200
    assert disable_response.json()["data"]["status"] == 0

    enable_response = client.put(f"/api/v1/knowledge/semantic-models/{model_id}/enable")
    assert enable_response.status_code == 200
    assert enable_response.json()["data"]["status"] == 1


def test_semantic_model_batch_import_upsert(client, db_session):
    agent_id = client.post("/api/v1/agents", json={"name": "sm-import-agent"}).json()["data"]["id"]
    datasource_id = client.post(
        "/api/v1/datasources",
        json={
            "name": "sm-import-datasource",
            "type": "sqlite",
            "host": "localhost",
            "port": 0,
            "database_name": ":memory:",
            "username": "",
            "password": "",
        },
    ).json()["data"]["id"]
    client.post(
        "/api/v1/datasources/agent-datasources",
        json={"agent_id": agent_id, "datasource_id": datasource_id, "is_active": 1},
    )

    import_response = client.post(
        "/api/v1/knowledge/semantic-models/batch-import",
        json={
            "agent_id": agent_id,
            "items": [
                {
                    "table_name": "orders",
                    "column_name": "amount",
                    "business_name": "订单金额",
                    "data_type": "decimal",
                },
                {
                    "table_name": "users",
                    "column_name": "id",
                    "business_name": "用户ID",
                    "data_type": "bigint",
                },
            ],
        },
    )
    assert import_response.status_code == 200
    result = import_response.json()["data"]
    assert result["total"] == 2
    assert result["success_count"] == 2
    assert result["fail_count"] == 0

    list_response = client.get("/api/v1/knowledge/semantic-models", params={"agent_id": agent_id})
    assert len(list_response.json()["data"]) == 2

    # Upsert: modify one, keep the other
    import_response2 = client.post(
        "/api/v1/knowledge/semantic-models/batch-import",
        json={
            "agent_id": agent_id,
            "items": [
                {
                    "table_name": "orders",
                    "column_name": "amount",
                    "business_name": "订单金额V2",
                    "data_type": "decimal",
                }
            ],
        },
    )
    assert import_response2.status_code == 200
    list_response2 = client.get("/api/v1/knowledge/semantic-models", params={"agent_id": agent_id})
    names = {m["business_name"] for m in list_response2.json()["data"]}
    assert names == {"订单金额V2", "用户ID"}


def test_semantic_model_excel_import(client, db_session):
    agent_id = client.post("/api/v1/agents", json={"name": "sm-excel-agent"}).json()["data"]["id"]
    datasource_id = client.post(
        "/api/v1/datasources",
        json={
            "name": "sm-excel-datasource",
            "type": "sqlite",
            "host": "localhost",
            "port": 0,
            "database_name": ":memory:",
            "username": "",
            "password": "",
        },
    ).json()["data"]["id"]
    client.post(
        "/api/v1/datasources/agent-datasources",
        json={"agent_id": agent_id, "datasource_id": datasource_id, "is_active": 1},
    )

    excel_bytes = _make_excel_bytes(
        [
            ["orders", "amount", "订单金额", "decimal", "GMV", "", "", ""],
            ["users", "id", "用户ID", "bigint", "", "", "", ""],
            ["", "missing", "", "", "", "", "", ""],
        ]
    )

    response = client.post(
        "/api/v1/knowledge/semantic-models/import/excel",
        data={"agent_id": agent_id},
        files={
            "file": (
                "test.xlsx",
                io.BytesIO(excel_bytes),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    result = response.json()["data"]
    assert result["success_count"] == 2
    assert result["fail_count"] == 1


def test_semantic_model_template_download(client):
    response = client.get("/api/v1/knowledge/semantic-models/template/download")
    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_agent_knowledge_json_create_defaults(client, db_session):
    agent_id = client.post("/api/v1/agents", json={"name": "ak-json-agent"}).json()["data"]["id"]
    response = client.post(
        "/api/v1/knowledge/agent-knowledge",
        json={
            "agent_id": agent_id,
            "title": "JSON知识",
            "type": "DOCUMENT",
            "content": "some content",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["embedding_status"] == "PENDING"
    assert data["is_deleted"] == 0
    assert data["is_resource_cleaned"] == 0
    assert data["is_recall"] == 1
    assert data["splitter_type"] == "token"


def test_agent_knowledge_get_update_recall_delete(client, db_session, upload_dir):
    agent_id = client.post("/api/v1/agents", json={"name": "ak-crud-agent"}).json()["data"]["id"]
    create_response = client.post(
        "/api/v1/knowledge/agent-knowledge",
        json={
            "agent_id": agent_id,
            "title": "原始标题",
            "type": "QA",
            "question": "Q1",
            "content": "A1",
        },
    )
    knowledge_id = create_response.json()["data"]["id"]

    get_response = client.get(f"/api/v1/knowledge/agent-knowledge/{knowledge_id}")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["title"] == "原始标题"

    update_response = client.put(
        f"/api/v1/knowledge/agent-knowledge/{knowledge_id}",
        json={"title": "更新标题", "content": "A1-updated"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["title"] == "更新标题"

    recall_response = client.put(
        f"/api/v1/knowledge/agent-knowledge/{knowledge_id}/recall",
        json={"is_recall": 0},
    )
    assert recall_response.status_code == 200
    assert recall_response.json()["data"]["is_recall"] == 0

    delete_response = client.delete(f"/api/v1/knowledge/agent-knowledge/{knowledge_id}")
    assert delete_response.status_code == 200

    get_after_delete = client.get(f"/api/v1/knowledge/agent-knowledge/{knowledge_id}")
    assert get_after_delete.status_code == 404


def test_agent_knowledge_multipart_document_success(client, db_session, upload_dir):
    agent_id = client.post("/api/v1/agents", json={"name": "ak-upload-agent"}).json()["data"]["id"]
    file_content = b"This is a test document for chunking."
    response = client.post(
        "/api/v1/knowledge/agent-knowledge/create",
        data={
            "agent_id": agent_id,
            "title": "上传文档",
            "type": "DOCUMENT",
            "splitter_type": "token",
        },
        files={"file": ("doc.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["source_filename"] == "doc.txt"
    assert data["file_size"] == len(file_content)
    assert data["file_type"] == "text/plain"
    assert data["file_path"].startswith("agent-knowledge/")

    # Verify physical file exists
    full_path = upload_dir / data["file_path"]
    assert full_path.exists()


def test_agent_knowledge_multipart_document_requires_file(client, db_session):
    agent_id = client.post("/api/v1/agents", json={"name": "ak-no-file-agent"}).json()["data"]["id"]
    response = client.post(
        "/api/v1/knowledge/agent-knowledge/create",
        data={
            "agent_id": agent_id,
            "title": "缺少文件",
            "type": "DOCUMENT",
        },
    )
    assert response.status_code == 400


def test_agent_knowledge_multipart_qa_requires_question_and_content(client, db_session):
    agent_id = client.post("/api/v1/agents", json={"name": "ak-qa-agent"}).json()["data"]["id"]
    response = client.post(
        "/api/v1/knowledge/agent-knowledge/create",
        data={
            "agent_id": agent_id,
            "title": "QA缺内容",
            "type": "QA",
            "question": "Q1",
        },
    )
    assert response.status_code == 400


def test_agent_knowledge_query_page(client, db_session):
    agent_id = client.post("/api/v1/agents", json={"name": "ak-page-agent"}).json()["data"]["id"]
    for i in range(3):
        client.post(
            "/api/v1/knowledge/agent-knowledge",
            json={
                "agent_id": agent_id,
                "title": f"知识{i}",
                "type": "QA",
                "question": f"问题{i}",
                "content": f"答案{i}",
            },
        )

    response = client.post(
        "/api/v1/knowledge/agent-knowledge/query/page",
        json={"agent_id": agent_id, "page": 1, "page_size": 2},
    )
    assert response.status_code == 200
    page = response.json()["data"]
    assert page["total"] == 3
    assert page["page"] == 1
    assert page["page_size"] == 2
    assert page["total_pages"] == 2
    assert len(page["items"]) == 2

    keyword_response = client.post(
        "/api/v1/knowledge/agent-knowledge/query/page",
        json={"agent_id": agent_id, "keyword": "知识1", "page": 1, "page_size": 10},
    )
    assert keyword_response.status_code == 200
    assert keyword_response.json()["data"]["total"] == 1


def test_agent_knowledge_retry_embedding_success(client, db_session):
    agent_id = client.post("/api/v1/agents", json={"name": "ak-retry-agent"}).json()["data"]["id"]
    create_response = client.post(
        "/api/v1/knowledge/agent-knowledge",
        json={
            "agent_id": agent_id,
            "title": "重试知识",
            "type": "QA",
            "question": "问题",
            "content": "答案",
        },
    )
    knowledge_id = create_response.json()["data"]["id"]

    retry_response = client.post(
        f"/api/v1/knowledge/agent-knowledge/{knowledge_id}/retry-embedding"
    )
    assert retry_response.status_code == 200
    data = retry_response.json()["data"]
    assert data["embedding_status"] == "COMPLETED"
    assert data["error_msg"] is None


def test_agent_knowledge_retry_embedding_rejects_processing(client, db_session):
    agent_id = client.post("/api/v1/agents", json={"name": "ak-processing-agent"}).json()["data"][
        "id"
    ]
    create_response = client.post(
        "/api/v1/knowledge/agent-knowledge",
        json={
            "agent_id": agent_id,
            "title": "处理中知识",
            "type": "QA",
            "question": "问题",
            "content": "答案",
        },
    )
    knowledge_id = create_response.json()["data"]["id"]

    from app.models.knowledge import AgentKnowledge

    row = db_session.query(AgentKnowledge).filter(AgentKnowledge.id == knowledge_id).first()
    row.embedding_status = "PROCESSING"
    db_session.commit()

    retry_response = client.post(
        f"/api/v1/knowledge/agent-knowledge/{knowledge_id}/retry-embedding"
    )
    assert retry_response.status_code == 400


def test_agent_knowledge_retry_embedding_rejects_not_recall(client, db_session):
    agent_id = client.post("/api/v1/agents", json={"name": "ak-norecall-agent"}).json()["data"][
        "id"
    ]
    create_response = client.post(
        "/api/v1/knowledge/agent-knowledge",
        json={
            "agent_id": agent_id,
            "title": "不召回知识",
            "type": "QA",
            "question": "问题",
            "content": "答案",
        },
    )
    knowledge_id = create_response.json()["data"]["id"]

    client.put(
        f"/api/v1/knowledge/agent-knowledge/{knowledge_id}/recall",
        json={"is_recall": 0},
    )

    retry_response = client.post(
        f"/api/v1/knowledge/agent-knowledge/{knowledge_id}/retry-embedding"
    )
    assert retry_response.status_code == 400
