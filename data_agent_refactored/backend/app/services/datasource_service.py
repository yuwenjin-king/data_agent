from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.models.datasource import Datasource, AgentDatasource, LogicalRelation
from app.schemas.datasource import DatasourceCreate, DatasourceUpdate, AgentDatasourceCreate, LogicalRelationCreate
from app.services.crud_base import CRUDBase


class CRUDDatasource(CRUDBase[Datasource, DatasourceCreate, DatasourceUpdate]):
    def get_by_name(self, db: Session, name: str) -> Optional[Datasource]:
        return db.query(Datasource).filter(Datasource.name == name).first()
    
    def get_multi_active(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Datasource]:
        return db.query(Datasource).filter(Datasource.status == "active").offset(skip).limit(limit).all()


class CRUDAgentDatasource(CRUDBase[AgentDatasource, AgentDatasourceCreate, AgentDatasourceCreate]):
    def get_by_agent_and_datasource(
        self, db: Session, agent_id: int, datasource_id: int
    ) -> Optional[AgentDatasource]:
        return db.query(AgentDatasource).filter(
            and_(
                AgentDatasource.agent_id == agent_id,
                AgentDatasource.datasource_id == datasource_id
            )
        ).first()
    
    def get_multi_by_agent(
        self, db: Session, *, agent_id: int, skip: int = 0, limit: int = 100
    ) -> List[AgentDatasource]:
        return db.query(AgentDatasource).filter(
            AgentDatasource.agent_id == agent_id
        ).offset(skip).limit(limit).all()


class CRUDLogicalRelation(CRUDBase[LogicalRelation, LogicalRelationCreate, LogicalRelationCreate]):
    def get_multi_by_datasource(
        self, db: Session, *, datasource_id: int, skip: int = 0, limit: int = 100
    ) -> List[LogicalRelation]:
        return db.query(LogicalRelation).filter(
            and_(
                LogicalRelation.datasource_id == datasource_id,
                LogicalRelation.is_deleted == False
            )
        ).offset(skip).limit(limit).all()


datasource_crud = CRUDDatasource(Datasource)
agent_datasource_crud = CRUDAgentDatasource(AgentDatasource)
logical_relation_crud = CRUDLogicalRelation(LogicalRelation)
