import json
import os
import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine, text

from app.utils.crypto import encrypt
from app.workflow.graph import build_workflow_graph
from app.workflow.llm.client import LLMClient
from app.workflow.llm.embedding import EmbeddingClient
from app.workflow.state import WorkflowState
from app.workflow.vectorstore.document import VectorDocument
from app.workflow.vectorstore.memory import InMemoryVectorStore


def _make_vector_store(datasource_id: int):
    store = InMemoryVectorStore()
    embed = EmbeddingClient._dummy_embedding
    store.add_documents(
        [
            VectorDocument(
                text="users user account member",
                embedding=embed("users user account member"),
                metadata={
                    "vector_type": "TABLE",
                    "datasource_id": datasource_id,
                    "table_name": "users",
                    "name": "users",
                },
            ),
            VectorDocument(
                text="users.id integer primary key",
                embedding=embed("users.id"),
                metadata={
                    "vector_type": "COLUMN",
                    "datasource_id": datasource_id,
                    "table_name": "users",
                    "column_name": "id",
                    "name": "id",
                    "data_type": "INTEGER",
                },
            ),
            VectorDocument(
                text="users.name varchar user name",
                embedding=embed("users.name"),
                metadata={
                    "vector_type": "COLUMN",
                    "datasource_id": datasource_id,
                    "table_name": "users",
                    "column_name": "name",
                    "name": "name",
                    "data_type": "VARCHAR",
                },
            ),
            VectorDocument(
                text="users.age integer user age",
                embedding=embed("users.age"),
                metadata={
                    "vector_type": "COLUMN",
                    "datasource_id": datasource_id,
                    "table_name": "users",
                    "column_name": "age",
                    "name": "age",
                    "data_type": "INTEGER",
                },
            ),
        ]
    )
    return store


def _mock_llm_client(responses: dict) -> LLMClient:
    """Create a mock LLMClient that returns canned responses based on prompt keywords."""
    config = type(
        "Config",
        (),
        {
            "provider": "mock",
            "base_url": "http://mock",
            "api_key": "mock",
            "model_name": "mock",
            "temperature": 0.0,
            "max_tokens": 2000,
            "completions_path": None,
            "embeddings_path": None,
            "proxy_enabled": False,
            "proxy_host": None,
            "proxy_port": None,
            "proxy_username": None,
            "proxy_password": None,
        },
    )()
    client = LLMClient(config)

    async def acomplete(messages, **kwargs):
        prompt = messages[0]["content"]
        for keyword, response in responses.items():
            if keyword in prompt:
                if isinstance(response, Exception):
                    raise response
                return response
        return ""

    client.acomplete = acomplete
    return client


@pytest.mark.asyncio
async def test_nl2sql_graph_with_sqlite_agent_db(db_session):
    # Create an agent datasource link and a real SQLite DB.
    from app.models.agent import Agent
    from app.models.datasource import AgentDatasource, Datasource

    agent = Agent(name="test-agent", status="published")
    db_session.add(agent)
    db_session.flush()

    sqlite_path = f"/tmp/test_agent_nl2sql_{uuid.uuid4().hex}.db"
    engine = create_engine(f"sqlite:///{sqlite_path}")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)"))
        conn.execute(text("INSERT INTO users (name, age) VALUES ('Alice', 30), ('Bob', 25)"))
        conn.commit()
    engine.dispose()

    datasource = Datasource(
        name="test-sqlite",
        type="sqlite",
        host="localhost",
        port=0,
        database_name="test",
        username="test",
        password=encrypt("test"),
        connection_url=f"sqlite:///{sqlite_path}",
        status="active",
    )
    db_session.add(datasource)
    db_session.flush()

    agent_datasource = AgentDatasource(
        agent_id=agent.id, datasource_id=datasource.id, is_active=True
    )
    db_session.add(agent_datasource)
    db_session.commit()

    vector_store = _make_vector_store(datasource.id)

    responses = {
        "意图分类": '{"classification": "data_analysis"}',
        "查询澄清与规范化": '{"canonical_query": "查询 users 表中的用户数量", "expanded_queries": []}',
        "需求可行性": (
            "【需求类型】：《数据分析》\n【语种类型】：《中文》\n"
            "【需求内容】：查询 users 表中的用户数量"
        ),
        "执行计划编排": (
            '{"thought_process":"单步取数","execution_plan":['
            '{"step":1,"tool_to_use":"sql_generate",'
            '"tool_parameters":{"instruction":"查询 users 表中的用户数量"}}]}'
        ),
        "语义一致性校验": "通过",
        "SQL 编写约束": "SELECT COUNT(*) AS cnt FROM users",
        "报告结构建议": "共有 2 位用户。",
    }
    llm_client = _mock_llm_client(responses)
    embedding_client = EmbeddingClient.dummy()

    graph = build_workflow_graph()
    initial_state: WorkflowState = {
        "agent_id": agent.id,
        "input": "有多少用户",
    }
    config = {
        "configurable": {
            "llm_client": llm_client,
            "embedding_client": embedding_client,
            "vector_store": vector_store,
            "db": db_session,
        }
    }

    final_state = None
    async for chunk in graph.astream(initial_state, config=config, stream_mode="updates"):
        for node_name, update in chunk.items():
            if node_name == "report_generator":
                final_state = update

    assert final_state is not None
    assert "result" in final_state
    assert "2" in final_state["result"] or "用户" in final_state["result"]

    # Cleanup
    os.remove(sqlite_path)


@pytest.mark.asyncio
async def test_planner_fallback_empty_sql_instruction_still_runs_sql(db_session):
    from app.models.agent import Agent
    from app.models.datasource import AgentDatasource, Datasource

    agent = Agent(name="fallback-agent", status="published")
    db_session.add(agent)
    db_session.flush()

    sqlite_path = f"/tmp/test_agent_planner_fallback_{uuid.uuid4().hex}.db"
    engine = create_engine(f"sqlite:///{sqlite_path}")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"))
        conn.execute(text("INSERT INTO users (name) VALUES ('Alice'), ('Bob')"))
        conn.commit()
    engine.dispose()

    datasource = Datasource(
        name="fallback-sqlite",
        type="sqlite",
        host="localhost",
        port=0,
        database_name="test",
        username="test",
        password=encrypt("test"),
        connection_url=f"sqlite:///{sqlite_path}",
        status="active",
    )
    db_session.add(datasource)
    db_session.flush()

    db_session.add(AgentDatasource(agent_id=agent.id, datasource_id=datasource.id, is_active=True))
    db_session.commit()

    responses = {
        "意图分类": '{"classification": "data_analysis"}',
        "查询澄清与规范化": '{"canonical_query": "查询 users 表中的用户数量", "expanded_queries": []}',
        "需求可行性": (
            "【需求类型】：《数据分析》\n【语种类型】：《中文》\n"
            "【需求内容】：查询 users 表中的用户数量"
        ),
        "执行计划编排": RuntimeError("planner failed"),
        "语义一致性校验": "通过",
        "SQL 编写约束": "SELECT COUNT(*) AS cnt FROM users",
        "报告结构建议": "共有 2 位用户。",
    }

    graph = build_workflow_graph()
    final_state = None
    async for chunk in graph.astream(
        {"agent_id": agent.id, "input": "有多少用户"},
        config={
            "configurable": {
                "llm_client": _mock_llm_client(responses),
                "embedding_client": EmbeddingClient.dummy(),
                "vector_store": _make_vector_store(datasource.id),
                "db": db_session,
            }
        },
        stream_mode="updates",
    ):
        for node_name, update in chunk.items():
            if node_name == "report_generator":
                final_state = update

    assert final_state is not None
    assert "2" in final_state["result"] or "用户" in final_state["result"]

    os.remove(sqlite_path)


@pytest.mark.asyncio
async def test_chitchat_graph():
    graph = build_workflow_graph()
    responses = {
        "意图分类": '{"classification": "chitchat"}',
    }
    llm_client = _mock_llm_client(responses)
    initial_state: WorkflowState = {"agent_id": 1, "input": "你好"}
    config = {"configurable": {"llm_client": llm_client}}

    final_state = None
    async for chunk in graph.astream(initial_state, config=config, stream_mode="updates"):
        for node_name, update in chunk.items():
            if node_name == "chitchat":
                final_state = update

    assert final_state is not None
    assert "Data Agent" in final_state["result"]
