from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.datasource import AgentDatasource, Datasource
from app.services.datasource_service import agent_datasource_crud
from app.utils.crypto import maybe_decrypt
from app.utils.db_introspection import build_sqlalchemy_url


def resolve_agent_datasource(db: Session, agent_id: int) -> Optional[AgentDatasource]:
    return agent_datasource_crud.get_active_by_agent(db, agent_id=agent_id)


def get_datasource_url_and_dialect(
    db: Session, agent_datasource: AgentDatasource
) -> Tuple[Optional[str], Optional[str]]:
    datasource = db.get(Datasource, agent_datasource.datasource_id)
    if not datasource:
        return None, None
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
    return url, datasource.type  # type: ignore[return-value]  # ORM Column[str]


def map_dialect_to_sql_dialect(datasource_type: Optional[str]) -> str:
    if not datasource_type:
        return "mysql"
    lowered = datasource_type.lower()
    if "postgres" in lowered:
        return "postgresql"
    if "sqlite" in lowered:
        return "sqlite"
    if "mysql" in lowered:
        return "mysql"
    if "sqlserver" in lowered or "mssql" in lowered:
        return "sqlserver"
    if "oracle" in lowered:
        return "oracle"
    if "hive" in lowered:
        return "hive"
    return lowered
