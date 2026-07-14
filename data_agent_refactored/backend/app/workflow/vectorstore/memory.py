from typing import Any, Dict, List, Optional

import numpy as np

from app.workflow.vectorstore.base import VectorStore
from app.workflow.vectorstore.document import VectorDocument


class InMemoryVectorStore(VectorStore):
    """Simple in-memory vector store using numpy cosine similarity."""

    def __init__(self) -> None:
        self.documents: List[VectorDocument] = []

    def clear(self) -> None:
        self.documents = []

    def add_documents(self, docs: List[VectorDocument]) -> None:
        for doc in docs:
            if not doc.embedding:
                raise ValueError(f"Document {doc.id} has no embedding")
        self.documents.extend(docs)

    def _matches(self, doc: VectorDocument, filter_expr: Optional[Dict[str, Any]]) -> bool:
        if not filter_expr:
            return True
        for key, value in filter_expr.items():
            if doc.metadata.get(key) != value:
                return False
        return True

    def similarity_search(
        self,
        query_embedding: List[float],
        filter_expr: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        threshold: Optional[float] = None,
    ) -> List[VectorDocument]:
        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []

        scored: List[tuple] = []
        for doc in self.documents:
            if not self._matches(doc, filter_expr):
                continue
            doc_vec = np.array(doc.embedding, dtype=np.float32)
            doc_norm = np.linalg.norm(doc_vec)
            if doc_norm == 0:
                continue
            similarity = float(np.dot(query_vec, doc_vec) / (query_norm * doc_norm))
            if threshold is not None and similarity < threshold:
                continue
            scored.append((similarity, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for similarity, doc in scored[:top_k]:
            result = VectorDocument(
                id=doc.id,
                text=doc.text,
                metadata=dict(doc.metadata),
                embedding=doc.embedding,
            )
            result.score = similarity
            results.append(result)
        return results

    def delete_by_metadata(self, filter_expr: Dict[str, Any]) -> int:
        original_count = len(self.documents)
        self.documents = [
            doc for doc in self.documents if not self._matches(doc, filter_expr)
        ]
        return original_count - len(self.documents)
