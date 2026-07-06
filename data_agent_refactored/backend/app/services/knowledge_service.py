from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import and_
from app.models.knowledge import SemanticModel, AgentKnowledge, AgentPresetQuestion
from app.schemas.knowledge import SemanticModelCreate, SemanticModelUpdate, AgentKnowledgeCreate, AgentPresetQuestionCreate
from app.services.crud_base import CRUDBase


class CRUDSemanticModel(CRUDBase[SemanticModel, SemanticModelCreate, SemanticModelUpdate]):
    def get_multi_by_agent(
        self, db: Session, *, agent_id: int, skip: int = 0, limit: int = 100
    ) -> List[SemanticModel]:
        return db.query(SemanticModel).filter(
            and_(
                SemanticModel.agent_id == agent_id,
                SemanticModel.status == True
            )
        ).offset(skip).limit(limit).all()
    
    def get_by_table(
        self, db: Session, *, agent_id: int, datasource_id: int, table_name: str
    ) -> List[SemanticModel]:
        return db.query(SemanticModel).filter(
            and_(
                SemanticModel.agent_id == agent_id,
                SemanticModel.datasource_id == datasource_id,
                SemanticModel.table_name == table_name,
                SemanticModel.status == True
            )
        ).all()


class CRUDAgentKnowledge(CRUDBase[AgentKnowledge, AgentKnowledgeCreate, AgentKnowledgeCreate]):
    def get_multi_by_agent(
        self, db: Session, *, agent_id: int, skip: int = 0, limit: int = 100
    ) -> List[AgentKnowledge]:
        return db.query(AgentKnowledge).filter(
            and_(
                AgentKnowledge.agent_id == agent_id,
                AgentKnowledge.is_deleted == 0
            )
        ).offset(skip).limit(limit).all()


class CRUDAgentPresetQuestion(CRUDBase[AgentPresetQuestion, AgentPresetQuestionCreate, AgentPresetQuestionCreate]):
    def get_multi_by_agent(
        self, db: Session, *, agent_id: int, skip: int = 0, limit: int = 100
    ) -> List[AgentPresetQuestion]:
        return db.query(AgentPresetQuestion).filter(
            and_(
                AgentPresetQuestion.agent_id == agent_id,
                AgentPresetQuestion.is_active == True
            )
        ).order_by(AgentPresetQuestion.sort_order).offset(skip).limit(limit).all()


semantic_model_crud = CRUDSemanticModel(SemanticModel)
agent_knowledge_crud = CRUDAgentKnowledge(AgentKnowledge)
agent_preset_question_crud = CRUDAgentPresetQuestion(AgentPresetQuestion)
