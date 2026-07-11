import asyncio
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.agent import BusinessKnowledge
from app.models.knowledge import AgentKnowledge
from app.workflow.llm.embedding import EmbeddingClient
from app.workflow.vectorstore.document import VectorDocument
from app.workflow.vectorstore.store import get_vector_store
from app.utils.chunking import chunk_text
from app.utils.db_introspection import list_columns, list_tables
from app.utils.file_storage import read_file_text


def _get_embedding_client() -> EmbeddingClient:
    # In production this should load from ModelConfig; for indexing we use dummy
    # if no active embedding model is configured to keep the app runnable.
    return EmbeddingClient.dummy()


def _delete_existing(vector_type: str, **filters) -> None:
    store = get_vector_store()
    store.delete_by_metadata({"vector_type": vector_type, **filters})


async def index_schema_documents(
    db: Session,
    datasource_id: int,
    url: str,
    agent_id: Optional[int] = None,
    table_names: Optional[List[str]] = None,
) -> None:
    """Index table and column schema documents for a datasource."""
    store = get_vector_store()
    embedding_client = _get_embedding_client()

    _delete_existing("TABLE", datasource_id=datasource_id)
    _delete_existing("COLUMN", datasource_id=datasource_id)

    tables = table_names or list_tables(url)
    table_docs: List[VectorDocument] = []
    column_docs: List[VectorDocument] = []

    for table_name in tables:
        table_text = f"表 {table_name}"
        table_docs.append(VectorDocument(
            text=table_text,
            metadata={
                "vector_type": "TABLE",
                "datasource_id": datasource_id,
                "table_name": table_name,
                "name": table_name,
            },
        ))

        try:
            columns = list_columns(url, table_name)
        except Exception:
            columns = []
        for column_name in columns:
            column_text = f"表 {table_name} 字段 {column_name}"
            column_docs.append(VectorDocument(
                text=column_text,
                metadata={
                    "vector_type": "COLUMN",
                    "datasource_id": datasource_id,
                    "table_name": table_name,
                    "column_name": column_name,
                    "name": column_name,
                },
            ))

    all_docs = table_docs + column_docs
    if not all_docs:
        return

    texts = [doc.text for doc in all_docs]
    embeddings = await embedding_client.embed(texts)
    for doc, embedding in zip(all_docs, embeddings):
        doc.embedding = embedding
    store.add_documents(all_docs)


async def index_business_knowledge(knowledge: BusinessKnowledge) -> None:
    """Index a business knowledge term."""
    if not knowledge.is_recall:
        return
    store = get_vector_store()
    embedding_client = _get_embedding_client()

    _delete_existing("BUSINESS_TERM", agent_id=knowledge.agent_id, business_term_id=knowledge.id)

    text = f"{knowledge.business_term}\n{knowledge.description or ''}\n{knowledge.synonyms or ''}"
    doc = VectorDocument(
        text=text,
        metadata={
            "vector_type": "BUSINESS_TERM",
            "agent_id": knowledge.agent_id,
            "business_term_id": knowledge.id,
        },
    )
    doc.embedding = (await embedding_client.embed([text]))[0]
    store.add_documents([doc])


async def index_agent_knowledge(knowledge: AgentKnowledge) -> None:
    """Index agent knowledge chunks."""
    if not knowledge.is_recall:
        return
    store = get_vector_store()
    embedding_client = _get_embedding_client()

    _delete_existing("AGENT_KNOWLEDGE", agent_id=knowledge.agent_id, knowledge_id=knowledge.id)

    content = knowledge.content or ""
    if not content and knowledge.file_path:
        try:
            content = read_file_text(knowledge.file_path)
        except Exception:
            content = ""

    chunks = chunk_text(content, splitter_type=knowledge.splitter_type or "token")
    docs = []
    for idx, chunk in enumerate(chunks):
        doc = VectorDocument(
            text=chunk,
            metadata={
                "vector_type": "AGENT_KNOWLEDGE",
                "agent_id": knowledge.agent_id,
                "knowledge_id": knowledge.id,
                "type": knowledge.type,
                "chunk_index": idx,
            },
        )
        docs.append(doc)

    if not docs:
        return

    embeddings = await embedding_client.embed([doc.text for doc in docs])
    for doc, embedding in zip(docs, embeddings):
        doc.embedding = embedding
    store.add_documents(docs)


def delete_agent_knowledge_index(knowledge_id: int) -> None:
    store = get_vector_store()
    store.delete_by_metadata({"vector_type": "AGENT_KNOWLEDGE", "knowledge_id": knowledge_id})


def delete_business_knowledge_index(knowledge_id: int) -> None:
    store = get_vector_store()
    store.delete_by_metadata({"vector_type": "BUSINESS_TERM", "business_term_id": knowledge_id})
