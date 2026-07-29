import uuid
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatSession, ModelConfig, UserPromptConfig
from app.schemas.chat import (
    ChatMessageCreate,
    ChatSessionCreate,
    ChatSessionUpdate,
    ModelConfigCreate,
    ModelConfigUpdate,
    UserPromptConfigCreate,
)
from app.services.crud_base import CRUDBase
from app.utils.crypto import encrypt


class CRUDChatSession(CRUDBase[ChatSession, ChatSessionCreate, ChatSessionUpdate]):
    def create(self, db: Session, obj_in: ChatSessionCreate) -> ChatSession:
        obj_data = obj_in.model_dump()
        obj_data["id"] = str(uuid.uuid4())
        db_obj = ChatSession(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_agent(
        self, db: Session, *, agent_id: int, skip: int = 0, limit: int = 100
    ) -> List[ChatSession]:
        return (
            db.query(ChatSession)
            .filter(and_(ChatSession.agent_id == agent_id, ChatSession.status != "deleted"))
            .order_by(ChatSession.is_pinned.desc(), ChatSession.update_time.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


class CRUDChatMessage(CRUDBase[ChatMessage, ChatMessageCreate, ChatMessageCreate]):
    def get_multi_by_session(
        self, db: Session, *, session_id: str, skip: int = 0, limit: int = 100
    ) -> List[ChatMessage]:
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.create_time)
            .offset(skip)
            .limit(limit)
            .all()
        )


class CRUDUserPromptConfig(
    CRUDBase[UserPromptConfig, UserPromptConfigCreate, UserPromptConfigCreate]
):
    def create(self, db: Session, obj_in: UserPromptConfigCreate) -> UserPromptConfig:
        obj_data = obj_in.model_dump()
        obj_data["id"] = str(uuid.uuid4())
        db_obj = UserPromptConfig(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_type(
        self,
        db: Session,
        *,
        prompt_type: str,
        agent_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserPromptConfig]:
        query = db.query(UserPromptConfig).filter(
            and_(UserPromptConfig.prompt_type == prompt_type, UserPromptConfig.enabled == True)
        )
        if agent_id is not None:
            query = query.filter(
                (UserPromptConfig.agent_id == agent_id) | (UserPromptConfig.agent_id == None)
            )
        return (
            query.order_by(UserPromptConfig.priority.desc(), UserPromptConfig.display_order)
            .offset(skip)
            .limit(limit)
            .all()
        )


class CRUDModelConfig(CRUDBase[ModelConfig, ModelConfigCreate, ModelConfigUpdate]):
    # Secret fields encrypted at rest; decrypted on use, masked in responses.
    _ENCRYPTED_FIELDS = ("api_key", "proxy_password")

    def create(self, db: Session, obj_in: ModelConfigCreate) -> ModelConfig:
        obj_data = self._dump_schema(obj_in)
        for field in self._ENCRYPTED_FIELDS:
            if obj_data.get(field):
                obj_data[field] = encrypt(obj_data[field])
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: ModelConfig, obj_in: ModelConfigUpdate) -> ModelConfig:
        obj_data = self._dump_schema(obj_in, exclude_unset=True)
        for field in self._ENCRYPTED_FIELDS:
            if obj_data.get(field):
                obj_data[field] = encrypt(obj_data[field])
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_active(self, db: Session) -> Optional[ModelConfig]:
        return (
            db.query(ModelConfig)
            .filter(and_(ModelConfig.is_active == True, ModelConfig.is_deleted == 0))
            .first()
        )

    def get_multi_by_type(
        self, db: Session, *, model_type: str, skip: int = 0, limit: int = 100
    ) -> List[ModelConfig]:
        return (
            db.query(ModelConfig)
            .filter(and_(ModelConfig.model_type == model_type, ModelConfig.is_deleted == 0))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def activate(self, db: Session, *, config_id: int) -> Optional[ModelConfig]:
        """Mark one model as active; deactivate other non-deleted configs of the same type.

        Chat / Embedding each keep at most one active config so the workflow
        registry can resolve a single client per role.
        """
        config = self.get(db, id=config_id)
        if not config or config.is_deleted:
            return None
        (
            db.query(ModelConfig)
            .filter(
                and_(
                    ModelConfig.model_type == config.model_type,
                    ModelConfig.is_deleted == 0,
                    ModelConfig.id != config.id,
                )
            )
            .update({"is_active": False}, synchronize_session=False)
        )
        config.is_active = True
        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    def deactivate(self, db: Session, *, config_id: int) -> Optional[ModelConfig]:
        config = self.get(db, id=config_id)
        if not config or config.is_deleted:
            return None
        config.is_active = False
        db.add(config)
        db.commit()
        db.refresh(config)
        return config


chat_session_crud = CRUDChatSession(ChatSession)
chat_message_crud = CRUDChatMessage(ChatMessage)
user_prompt_config_crud = CRUDUserPromptConfig(UserPromptConfig)
model_config_crud = CRUDModelConfig(ModelConfig)
