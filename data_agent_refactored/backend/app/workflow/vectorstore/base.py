from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.workflow.vectorstore.document import VectorDocument


class VectorStore(ABC):
    """Pluggable vector store interface."""

    @abstractmethod
    def add_documents(self, docs: List[VectorDocument]) -> None:
        raise NotImplementedError

    @abstractmethod
    def similarity_search(
        self,
        query_embedding: List[float],
        filter_expr: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        threshold: Optional[float] = None,
    ) -> List[VectorDocument]:
        raise NotImplementedError

    @abstractmethod
    def delete_by_metadata(self, filter_expr: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError
