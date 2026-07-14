from app.workflow.vectorstore.memory import InMemoryVectorStore

_vector_store: InMemoryVectorStore | None = None


def get_vector_store() -> InMemoryVectorStore:
    """Return the application-wide in-memory vector store singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = InMemoryVectorStore()
    return _vector_store


def reset_vector_store() -> None:
    """Reset the vector store. Useful for tests."""
    global _vector_store
    _vector_store = InMemoryVectorStore()
