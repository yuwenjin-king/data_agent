from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.models.agent import Agent, BusinessKnowledge
from app.schemas.agent import AgentCreate, AgentUpdate, BusinessKnowledgeCreate, BusinessKnowledgeUpdate
from app.services.crud_base import CRUDBase


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
