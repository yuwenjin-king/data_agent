from app.core.config import settings
from app.workflow.vectorstore.base import VectorStore
from app.workflow.vectorstore.memory import InMemoryVectorStore
from app.workflow.vectorstore.persistent import PersistentVectorStore

_vector_store: VectorStore | None = None


def _build_vector_store() -> VectorStore:
    if settings.VECTOR_STORE_TYPE == "persistent":
        return PersistentVectorStore(settings.VECTOR_STORE_PATH)
    return InMemoryVectorStore()


def get_vector_store() -> VectorStore:
    """Return the application-wide vector store singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = _build_vector_store()
    return _vector_store


def reset_vector_store() -> None:
    """Reset the vector store. Useful for tests."""
    global _vector_store
    _vector_store = _build_vector_store()
