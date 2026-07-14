import pytest
from sqlalchemy import create_engine, text

from app.models.agent import Agent
from app.models.datasource import AgentDatasource, Datasource
from app.models.knowledge import AgentKnowledge
from app.schemas.agent import BusinessKnowledgeCreate
from app.schemas.knowledge import AgentKnowledgeCreate
from app.services.agent_service import business_knowledge_crud
from app.services.knowledge_service import agent_knowledge_crud
from app.utils.crypto import encrypt
from app.workflow.vectorstore.store import get_vector_store, reset_vector_store


def test_schema_indexing_via_init_schema(client, db_session):
    reset_vector_store()

    agent = Agent(name="schema-agent", status="published")
    db_session.add(agent)
    db_session.flush()

    sqlite_path = f"/tmp/test_indexing_{__import__('uuid').uuid4().hex}.db"
    engine = create_engine(f"sqlite:///{sqlite_path}")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT)"))
        conn.commit()
    engine.dispose()

    datasource = Datasource(
        name="indexing-sqlite",
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

    response = client.post(
        f"/api/v1/agents/{agent.id}/datasources/init-schema",
        json={"table_names": ["products"]},
    )
    assert response.status_code == 200

    store = get_vector_store()
    table_docs = store.similarity_search(
        [1.0] + [0.0] * 1535,
        filter_expr={"vector_type": "TABLE", "datasource_id": datasource.id},
        top_k=10,
    )
    assert any(doc.metadata.get("table_name") == "products" for doc in table_docs)

    import os

    os.remove(sqlite_path)


def test_business_knowledge_indexing(db_session):
    reset_vector_store()

    agent = Agent(name="bk-agent", status="published")
    db_session.add(agent)
    db_session.flush()

    knowledge = business_knowledge_crud.create(
        db_session,
        obj_in=BusinessKnowledgeCreate(
            agent_id=agent.id,
            business_term="核心用户",
            description="最近30天消费超过5000元的用户",
            synonyms="VIP用户",
            is_recall=True,
        ),
    )

    # Trigger indexing manually (normally done in router).
    import asyncio

    from app.workflow.indexing import index_business_knowledge

    asyncio.run(index_business_knowledge(knowledge))

    store = get_vector_store()
    docs = store.similarity_search(
        [1.0] + [0.0] * 1535,
        filter_expr={"vector_type": "BUSINESS_TERM", "agent_id": agent.id},
        top_k=10,
    )
    assert any("核心用户" in doc.text for doc in docs)


def test_agent_knowledge_indexing(db_session):
    reset_vector_store()

    agent = Agent(name="ak-agent", status="published")
    db_session.add(agent)
    db_session.flush()

    knowledge = agent_knowledge_crud.create(
        db_session,
        obj_in=AgentKnowledgeCreate(
            agent_id=agent.id,
            title="退款政策",
            type="DOCUMENT",
            content="退款需要在7天内申请。",
            is_recall=True,
            splitter_type="token",
        ),
    )

    import asyncio

    from app.workflow.indexing import index_agent_knowledge

    asyncio.run(index_agent_knowledge(knowledge))

    store = get_vector_store()
    docs = store.similarity_search(
        [1.0] + [0.0] * 1535,
        filter_expr={"vector_type": "AGENT_KNOWLEDGE", "agent_id": agent.id},
        top_k=10,
    )
    assert any("退款" in doc.text for doc in docs)
