from typing import Optional
from sqlalchemy.orm import Session

from app.models.chat import ModelConfig
from app.workflow.llm.client import LLMClient
from app.workflow.llm.embedding import EmbeddingClient


def get_chat_client(db: Session) -> Optional[LLMClient]:
    """Load the active CHAT ModelConfig and return an LLMClient."""
    config = (
        db.query(ModelConfig)
        .filter(ModelConfig.is_active.is_(True), ModelConfig.is_deleted == 0)
        .first()
    )
    if not config:
        return None
    return LLMClient(config)


def get_embedding_client(db: Session) -> EmbeddingClient:
    """Load the active EMBEDDING ModelConfig and return an EmbeddingClient.

    Falls back to dummy embeddings if no config is active.
    """
    config = (
        db.query(ModelConfig)
        .filter(
            ModelConfig.model_type == "EMBEDDING",
            ModelConfig.is_active.is_(True),
            ModelConfig.is_deleted == 0,
        )
        .first()
    )
    if not config:
        return EmbeddingClient.dummy()
    return EmbeddingClient(config)


def get_model_config(db: Session, model_type: str) -> Optional[ModelConfig]:
    """Load the active ModelConfig of the given type."""
    return (
        db.query(ModelConfig)
        .filter(
            ModelConfig.model_type == model_type,
            ModelConfig.is_active.is_(True),
            ModelConfig.is_deleted == 0,
        )
        .first()
    )
