import re
from typing import List

from app.workflow.vectorstore.document import VectorDocument


def keyword_score(query: str, text: str) -> float:
    """Simple keyword overlap score between query and document text."""
    query_tokens = set(re.findall(r"\w+", query.lower()))
    text_tokens = set(re.findall(r"\w+", text.lower()))
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens & text_tokens)
    return overlap / len(query_tokens)


def hybrid_search(
    query: str,
    query_embedding: List[float],
    docs: List[VectorDocument],
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3,
    top_k: int = 5,
) -> List[VectorDocument]:
    """Re-rank a list of vector documents with a weighted vector + keyword score."""
    scored = []
    for doc in docs:
        vec_score = doc.score if doc.score is not None else 0.0
        kw_score = keyword_score(query, doc.text)
        combined = vector_weight * vec_score + keyword_weight * kw_score
        scored.append((combined, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, doc in scored[:top_k]:
        result = VectorDocument(
            id=doc.id,
            text=doc.text,
            metadata=dict(doc.metadata),
            embedding=doc.embedding,
        )
        result.score = score
        results.append(result)
    return results
