import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class VectorDocument:
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    embedding: Optional[list] = None
    score: Optional[float] = None

    @property
    def vector_type(self) -> Optional[str]:
        return self.metadata.get("vector_type")

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VectorDocument):
            return NotImplemented
        return self.id == other.id
