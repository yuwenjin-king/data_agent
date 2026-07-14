from typing import Optional

from langchain_core.runnables import RunnableConfig

from app.workflow.llm.embedding import EmbeddingClient
from app.workflow.prompts.loader import PromptLoader
from app.workflow.state import WorkflowState
from app.workflow.vectorstore.base import VectorStore


async def evidence_recall_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    configurable = (config or {}).get("configurable", {})
    embedding_client: EmbeddingClient = (
        configurable.get("embedding_client") or EmbeddingClient.dummy()
    )
    vector_store: Optional[VectorStore] = configurable.get("vector_store")
    agent_id = state.get("agent_id")
    query = state.get("input", "")

    if not vector_store:
        return {"evidence": ""}

    query_embedding = (await embedding_client.embed([query]))[0]

    business_docs = vector_store.similarity_search(
        query_embedding=query_embedding,
        filter_expr={"vector_type": "BUSINESS_TERM", "agent_id": agent_id},
        top_k=3,
    )
    agent_docs = vector_store.similarity_search(
        query_embedding=query_embedding,
        filter_expr={"vector_type": "AGENT_KNOWLEDGE", "agent_id": agent_id},
        top_k=3,
    )

    loader = PromptLoader()
    parts = []
    if business_docs:
        business_text = "\n".join(f"- {doc.text}" for doc in business_docs)
        parts.append(loader.render("business-knowledge", business_knowledge=business_text))
    if agent_docs:
        agent_text = "\n".join(f"- {doc.text}" for doc in agent_docs)
        parts.append(loader.render("agent-knowledge", agent_knowledge=agent_text))

    evidence = "\n\n".join(parts) if parts else ""
    return {"evidence": evidence}
