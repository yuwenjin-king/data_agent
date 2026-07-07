from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.models.datasource import Datasource, AgentDatasource, LogicalRelation, AgentDatasourceTables
from app.schemas.datasource import (
    DatasourceCreate, DatasourceUpdate, AgentDatasourceCreate,
    LogicalRelationCreate, DatasourceTestResponse, InitSchemaRequest
)
from app.services.crud_base import CRUDBase
from app.utils.crypto import encrypt, maybe_decrypt
from app.utils.db_introspection import build_sqlalchemy_url, test_connection, list_tables, list_columns


SUPPORTED_DATASOURCE_TYPES = [
    {"type": "mysql", "name": "MySQL", "description": "MySQL 关系型数据库"},
    {"type": "postgresql", "name": "PostgreSQL", "description": "PostgreSQL 关系型数据库"},
    {"type": "sqlite", "name": "SQLite", "description": "SQLite 本地数据库"},
    {"type": "dameng", "name": "Dameng", "description": "达梦数据库"},
    {"type": "sqlserver", "name": "SQL Server", "description": "Microsoft SQL Server"},
    {"type": "oracle", "name": "Oracle", "description": "Oracle 数据库"},
    {"type": "hive", "name": "Hive", "description": "Apache Hive"},
]


class CRUDDatasource(CRUDBase[Datasource, DatasourceCreate, DatasourceUpdate]):
    def get_by_name(self, db: Session, name: str) -> Optional[Datasource]:
        return db.query(Datasource).filter(Datasource.name == name).first()

    def get_multi_active(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Datasource]:
        return db.query(Datasource).filter(Datasource.status == "active").offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: DatasourceCreate) -> Datasource:
        obj_data = self._dump_schema(obj_in)
        if obj_data.get("password"):
            obj_data["password"] = encrypt(obj_data["password"])
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Datasource, obj_in: DatasourceUpdate) -> Datasource:
        obj_data = self._dump_schema(obj_in, exclude_unset=True)
        if obj_data.get("password"):
            obj_data["password"] = encrypt(obj_data["password"])
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def test_connection(self, db: Session, *, datasource_id: int) -> DatasourceTestResponse:
        datasource = self.get(db, id=datasource_id)
        if not datasource:
            return DatasourceTestResponse(success=False, message="Datasource not found")

        password = maybe_decrypt(datasource.password) or ""
        try:
            url = build_sqlalchemy_url(
                type=datasource.type,
                host=datasource.host,
                port=datasource.port,
                database_name=datasource.database_name,
                username=datasource.username,
                password=password,
                connection_url=datasource.connection_url,
            )
        except ValueError as exc:
            datasource.test_status = "failed"
            db.add(datasource)
            db.commit()
            return DatasourceTestResponse(success=False, message=str(exc))

        ok, message = test_connection(url)
        datasource.test_status = "success" if ok else "failed"
        db.add(datasource)
        db.commit()
        db.refresh(datasource)
        return DatasourceTestResponse(success=ok, message=message)

    def list_tables(self, db: Session, *, datasource_id: int) -> List[str]:
        datasource = self.get(db, id=datasource_id)
        if not datasource:
            raise ValueError("Datasource not found")
        password = maybe_decrypt(datasource.password) or ""
        url = build_sqlalchemy_url(
            type=datasource.type,
            host=datasource.host,
            port=datasource.port,
            database_name=datasource.database_name,
            username=datasource.username,
            password=password,
            connection_url=datasource.connection_url,
        )
        return list_tables(url)

    def list_columns(self, db: Session, *, datasource_id: int, table_name: str) -> List[str]:
        datasource = self.get(db, id=datasource_id)
        if not datasource:
            raise ValueError("Datasource not found")
        password = maybe_decrypt(datasource.password) or ""
        url = build_sqlalchemy_url(
            type=datasource.type,
            host=datasource.host,
            port=datasource.port,
            database_name=datasource.database_name,
            username=datasource.username,
            password=password,
            connection_url=datasource.connection_url,
        )
        return list_columns(url, table_name)

    def get_supported_types(self) -> List[dict]:
        return SUPPORTED_DATASOURCE_TYPES


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

    def get_active_by_agent(self, db: Session, *, agent_id: int) -> Optional[AgentDatasource]:
        return db.query(AgentDatasource).filter(
            and_(
                AgentDatasource.agent_id == agent_id,
                AgentDatasource.is_active == 1
            )
        ).first()

    def init_schema(self, db: Session, *, agent_id: int, table_names: List[str]) -> Optional[AgentDatasource]:
        link = self.get_active_by_agent(db, agent_id=agent_id)
        if not link:
            link = db.query(AgentDatasource).filter(
                AgentDatasource.agent_id == agent_id
            ).order_by(AgentDatasource.create_time.desc()).first()
        if not link:
            return None

        db.query(AgentDatasourceTables).filter(
            AgentDatasourceTables.agent_datasource_id == link.id
        ).delete()

        for table_name in table_names:
            db.add(AgentDatasourceTables(
                agent_datasource_id=link.id,
                table_name=table_name
            ))
        db.commit()
        db.refresh(link)
        return link


class CRUDLogicalRelation(CRUDBase[LogicalRelation, LogicalRelationCreate, LogicalRelationCreate]):
    def get_multi_by_datasource(
        self, db: Session, *, datasource_id: int, skip: int = 0, limit: int = 100
    ) -> List[LogicalRelation]:
        return db.query(LogicalRelation).filter(
            and_(
                LogicalRelation.datasource_id == datasource_id,
                LogicalRelation.is_deleted == 0
            )
        ).offset(skip).limit(limit).all()


datasource_crud = CRUDDatasource(Datasource)
agent_datasource_crud = CRUDAgentDatasource(AgentDatasource)
logical_relation_crud = CRUDLogicalRelation(LogicalRelation)
