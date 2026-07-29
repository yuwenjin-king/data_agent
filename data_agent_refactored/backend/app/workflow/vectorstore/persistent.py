import json
import os
import tempfile
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List

from app.workflow.vectorstore.document import VectorDocument
from app.workflow.vectorstore.memory import InMemoryVectorStore


class PersistentVectorStore(InMemoryVectorStore):
    """JSONL-backed vector store for durable single-process deployments."""

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = Path(path)
        self._lock = Lock()
        self._load()

    def add_documents(self, docs: List[VectorDocument]) -> None:
        with self._lock:
            super().add_documents(docs)
            self._persist()

    def delete_by_metadata(self, filter_expr: Dict[str, Any]) -> int:
        with self._lock:
            deleted = super().delete_by_metadata(filter_expr)
            if deleted:
                self._persist()
            return deleted

    def clear(self) -> None:
        with self._lock:
            super().clear()
            self._persist()

    def _load(self) -> None:
        if not self.path.exists():
            return
        documents: list[VectorDocument] = []
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                documents.append(
                    VectorDocument(
                        id=payload["id"],
                        text=payload["text"],
                        metadata=payload.get("metadata") or {},
                        embedding=payload.get("embedding"),
                    )
                )
        self.documents = documents

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.path.parent,
            delete=False,
        ) as tmp:
            tmp_path = Path(tmp.name)
            for doc in self.documents:
                tmp.write(
                    json.dumps(
                        {
                            "id": doc.id,
                            "text": doc.text,
                            "metadata": doc.metadata,
                            "embedding": doc.embedding,
                        },
                        ensure_ascii=False,
                        default=str,
                    )
                    + "\n"
                )
        os.replace(tmp_path, self.path)
