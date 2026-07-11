from typing import List, Optional

from langchain_core.runnables import RunnableConfig
from sqlalchemy.orm import Session

from app.workflow.llm.embedding import EmbeddingClient
from app.workflow.sql.utils import resolve_agent_datasource
from app.workflow.state import WorkflowState
from app.workflow.vectorstore.base import VectorStore
from app.workflow.vectorstore.document import VectorDocument


async def schema_recall_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    configurable = (config or {}).get("configurable", {})
    embedding_client: EmbeddingClient = configurable.get("embedding_client") or EmbeddingClient.dummy()
    vector_store: Optional[VectorStore] = configurable.get("vector_store")
    db: Optional[Session] = configurable.get("db")

    query_enhance_output = state.get("query_enhance_node_output")
    canonical_query = query_enhance_output.canonical_query if query_enhance_output else state.get("input", "")
    agent_id = state.get("agent_id")

    if not vector_store or not db:
        return {"table_documents_for_schema": [], "column_documents_for_schema": []}

    agent_datasource = resolve_agent_datasource(db, agent_id)
    if not agent_datasource:
        return {"table_documents_for_schema": [], "column_documents_for_schema": []}

    datasource_id = agent_datasource.datasource_id
    query_embedding = (await embedding_client.embed([canonical_query]))[0]

    table_docs = vector_store.similarity_search(
        query_embedding=query_embedding,
        filter_expr={"vector_type": "TABLE", "datasource_id": datasource_id},
        top_k=5,
    )

    recalled_table_names = [doc.metadata.get("table_name") or doc.metadata.get("name") for doc in table_docs]
    recalled_table_names = [name for name in recalled_table_names if name]

    column_docs: List[VectorDocument] = []
    if recalled_table_names:
        # Retrieve columns for recalled tables. We do a broad search and filter.
        all_column_docs = vector_store.similarity_search(
            query_embedding=query_embedding,
            filter_expr={"vector_type": "COLUMN", "datasource_id": datasource_id},
            top_k=50,
        )
        column_docs = [
            doc for doc in all_column_docs
            if doc.metadata.get("table_name") in recalled_table_names
        ]

    return {
        "table_documents_for_schema": table_docs,
        "column_documents_for_schema": column_docs,
    }
