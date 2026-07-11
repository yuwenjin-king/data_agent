import pytest

from app.workflow.vectorstore.document import VectorDocument
from app.workflow.vectorstore.memory import InMemoryVectorStore
from app.workflow.retrieval.hybrid import hybrid_search


def embed_user():
    vec = [0.0] * 1536
    vec[0] = 1.0
    return vec


def embed_order():
    vec = [0.0] * 1536
    vec[1] = 1.0
    return vec


def test_add_and_search():
    store = InMemoryVectorStore()
    docs = [
        VectorDocument(text="user table has id and name", embedding=embed_user()),
        VectorDocument(text="order table has id and amount", embedding=embed_order()),
    ]
    store.add_documents(docs)
    query = [0.99] + [0.0] * 1535  # close to user embedding
    results = store.similarity_search(query, top_k=1)
    assert len(results) == 1
    assert "user" in results[0].text.lower()


def test_metadata_filter():
    store = InMemoryVectorStore()
    docs = [
        VectorDocument(text="user table", embedding=embed_user(), metadata={"agent_id": 1}),
        VectorDocument(text="order table", embedding=embed_order(), metadata={"agent_id": 2}),
    ]
    store.add_documents(docs)
    query = [0.0] * 1536
    query[1] = 1.0
    results = store.similarity_search(query, filter_expr={"agent_id": 2}, top_k=5)
    assert len(results) == 1
    assert "order" in results[0].text.lower()


def test_hybrid_search_rerank():
    docs = [
        VectorDocument(text="user table has id and name", embedding=embed_user(), score=0.9),
        VectorDocument(text="order table has id and amount", embedding=embed_order(), score=0.95),
    ]
    query_embedding = embed_order()
    results = hybrid_search("order amount", query_embedding, docs, top_k=2)
    # Keyword-heavy doc should win despite slightly lower vector score.
    assert "order" in results[0].text.lower()


def test_delete_by_metadata():
    store = InMemoryVectorStore()
    docs = [
        VectorDocument(text="a", embedding=embed_user(), metadata={"agent_id": 1}),
        VectorDocument(text="b", embedding=embed_user(), metadata={"agent_id": 1}),
        VectorDocument(text="c", embedding=embed_order(), metadata={"agent_id": 2}),
    ]
    store.add_documents(docs)
    deleted = store.delete_by_metadata({"agent_id": 1})
    assert deleted == 2
    assert len(store.documents) == 1
