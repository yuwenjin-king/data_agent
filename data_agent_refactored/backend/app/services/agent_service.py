from typing import List, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.agent import Agent, BusinessKnowledge
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    BusinessKnowledgeCreate,
    BusinessKnowledgeUpdate,
)
from app.services.crud_base import CRUDBase
from app.utils.api_key import generate_api_key, mask_api_key
from app.utils.crypto import encrypt


class CRUDAgent(CRUDBase[Agent, AgentCreate, AgentUpdate]):
    def get_by_name(self, db: Session, name: str) -> Optional[Agent]:
        return db.query(Agent).filter(Agent.name == name).first()

    def get_multi_by_status(
        self, db: Session, *, status: str, skip: int = 0, limit: int = 100
    ) -> List[Agent]:
        return db.query(Agent).filter(Agent.status == status).offset(skip).limit(limit).all()

    def search(
        self, db: Session, *, keyword: str, skip: int = 0, limit: int = 100
    ) -> List[Agent]:
        return db.query(Agent).filter(
            (Agent.name.contains(keyword)) | (Agent.description.contains(keyword))
        ).offset(skip).limit(limit).all()

    def publish(self, db: Session, *, agent_id: int) -> Optional[Agent]:
        agent = self.get(db, id=agent_id)
        if not agent:
            return None
        agent.status = "published"
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    def offline(self, db: Session, *, agent_id: int) -> Optional[Agent]:
        agent = self.get(db, id=agent_id)
        if not agent:
            return None
        agent.status = "offline"
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    def generate_api_key(self, db: Session, *, agent_id: int) -> Tuple[Optional[Agent], Optional[str]]:
        agent = self.get(db, id=agent_id)
        if not agent:
            return None, None
        raw_key = generate_api_key()
        agent.api_key = encrypt(raw_key)
        agent.api_key_enabled = 1
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent, raw_key

    def delete_api_key(self, db: Session, *, agent_id: int) -> Optional[Agent]:
        agent = self.get(db, id=agent_id)
        if not agent:
            return None
        agent.api_key = None
        agent.api_key_enabled = 0
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    def set_api_key_enabled(self, db: Session, *, agent_id: int, enabled: int) -> Optional[Agent]:
        agent = self.get(db, id=agent_id)
        if not agent:
            return None
        agent.api_key_enabled = 1 if enabled else 0
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    def get_api_key_masked(self, db: Session, *, agent_id: int) -> Tuple[Optional[str], Optional[int]]:
        agent = self.get(db, id=agent_id)
        if not agent:
            return None, None
        from app.utils.crypto import maybe_decrypt
        return mask_api_key(maybe_decrypt(agent.api_key)), agent.api_key_enabled


class CRUDBusinessKnowledge(CRUDBase[BusinessKnowledge, BusinessKnowledgeCreate, BusinessKnowledgeUpdate]):
    def get_multi_by_agent(
        self, db: Session, *, agent_id: int, skip: int = 0, limit: int = 100
    ) -> List[BusinessKnowledge]:
        return db.query(BusinessKnowledge).filter(
            and_(
                BusinessKnowledge.agent_id == agent_id,
                BusinessKnowledge.is_deleted == 0
            )
        ).offset(skip).limit(limit).all()


agent_crud = CRUDAgent(Agent)
business_knowledge_crud = CRUDBusinessKnowledge(BusinessKnowledge)
