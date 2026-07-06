from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import and_
import uuid
from app.models.chat import ChatSession, ChatMessage, UserPromptConfig, ModelConfig
from app.schemas.chat import ChatSessionCreate, ChatSessionUpdate, ChatMessageCreate, UserPromptConfigCreate, ModelConfigCreate, ModelConfigUpdate
from app.services.crud_base import CRUDBase


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
        return db.query(ChatSession).filter(
            and_(
                ChatSession.agent_id == agent_id,
                ChatSession.status != "deleted"
            )
        ).order_by(ChatSession.is_pinned.desc(), ChatSession.update_time.desc()).offset(skip).limit(limit).all()


class CRUDChatMessage(CRUDBase[ChatMessage, ChatMessageCreate, ChatMessageCreate]):
    def get_multi_by_session(
        self, db: Session, *, session_id: str, skip: int = 0, limit: int = 100
    ) -> List[ChatMessage]:
        return db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.create_time).offset(skip).limit(limit).all()


class CRUDUserPromptConfig(CRUDBase[UserPromptConfig, UserPromptConfigCreate, UserPromptConfigCreate]):
    def create(self, db: Session, obj_in: UserPromptConfigCreate) -> UserPromptConfig:
        obj_data = obj_in.model_dump()
        obj_data["id"] = str(uuid.uuid4())
        db_obj = UserPromptConfig(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_multi_by_type(
        self, db: Session, *, prompt_type: str, agent_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[UserPromptConfig]:
        query = db.query(UserPromptConfig).filter(
            and_(
                UserPromptConfig.prompt_type == prompt_type,
                UserPromptConfig.enabled == True
            )
        )
        if agent_id is not None:
            query = query.filter(
                (UserPromptConfig.agent_id == agent_id) | (UserPromptConfig.agent_id == None)
            )
        return query.order_by(UserPromptConfig.priority.desc(), UserPromptConfig.display_order).offset(skip).limit(limit).all()


class CRUDModelConfig(CRUDBase[ModelConfig, ModelConfigCreate, ModelConfigUpdate]):
    def get_active(self, db: Session) -> Optional[ModelConfig]:
        return db.query(ModelConfig).filter(
            and_(
                ModelConfig.is_active == True,
                ModelConfig.is_deleted == 0
            )
        ).first()
    
    def get_multi_by_type(
        self, db: Session, *, model_type: str, skip: int = 0, limit: int = 100
    ) -> List[ModelConfig]:
        return db.query(ModelConfig).filter(
            and_(
                ModelConfig.model_type == model_type,
                ModelConfig.is_deleted == 0
            )
        ).offset(skip).limit(limit).all()


chat_session_crud = CRUDChatSession(ChatSession)
chat_message_crud = CRUDChatMessage(ChatMessage)
user_prompt_config_crud = CRUDUserPromptConfig(UserPromptConfig)
model_config_crud = CRUDModelConfig(ModelConfig)
