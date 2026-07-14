from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.datasource import (
    AgentDatasourceCreate,
    AgentDatasourceResponse,
    DatasourceCreate,
    DatasourceResponse,
    DatasourceTestResponse,
    DatasourceTypeResponse,
    DatasourceUpdate,
    LogicalRelationCreate,
    LogicalRelationResponse,
)
from app.services.datasource_service import (
    agent_datasource_crud,
    datasource_crud,
    logical_relation_crud,
)

router = APIRouter(prefix="/datasources", tags=["datasources"])


@router.post("", response_model=ApiResponse[DatasourceResponse])
def create_datasource(datasource_in: DatasourceCreate, db: Session = Depends(get_db)):
    datasource = datasource_crud.create(db, obj_in=datasource_in)
    return ApiResponse(data=DatasourceResponse.model_validate(datasource))


@router.get("/types", response_model=ApiResponse[List[DatasourceTypeResponse]])
def list_datasource_types(db: Session = Depends(get_db)):
    types = datasource_crud.get_supported_types()
    return ApiResponse(data=[DatasourceTypeResponse(**t) for t in types])


@router.get("/{datasource_id}", response_model=ApiResponse[DatasourceResponse])
def get_datasource(datasource_id: int, db: Session = Depends(get_db)):
    datasource = datasource_crud.get(db, id=datasource_id)
    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found")
    return ApiResponse(data=DatasourceResponse.model_validate(datasource))


@router.get("", response_model=ApiResponse[List[DatasourceResponse]])
def list_datasources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    datasources = datasource_crud.get_multi(db, skip=skip, limit=limit)
    return ApiResponse(data=[DatasourceResponse.model_validate(d) for d in datasources])


@router.put("/{datasource_id}", response_model=ApiResponse[DatasourceResponse])
def update_datasource(
    datasource_id: int, datasource_in: DatasourceUpdate, db: Session = Depends(get_db)
):
    datasource = datasource_crud.get(db, id=datasource_id)
    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found")
    datasource = datasource_crud.update(db, db_obj=datasource, obj_in=datasource_in)
    return ApiResponse(data=DatasourceResponse.model_validate(datasource))


@router.delete("/{datasource_id}", response_model=ApiResponse)
def delete_datasource(datasource_id: int, db: Session = Depends(get_db)):
    datasource = datasource_crud.get(db, id=datasource_id)
    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found")
    datasource_crud.remove(db, id=datasource_id)
    return ApiResponse(message="Datasource deleted successfully")


@router.post("/{datasource_id}/test", response_model=ApiResponse[DatasourceTestResponse])
def test_datasource_connection(datasource_id: int, db: Session = Depends(get_db)):
    datasource = datasource_crud.get(db, id=datasource_id)
    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found")
    result = datasource_crud.test_connection(db, datasource_id=datasource_id)
    return ApiResponse(data=result)


@router.get("/{datasource_id}/tables", response_model=ApiResponse[List[str]])
def list_datasource_tables(datasource_id: int, db: Session = Depends(get_db)):
    datasource = datasource_crud.get(db, id=datasource_id)
    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found")
    try:
        tables = datasource_crud.list_tables(db, datasource_id=datasource_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ApiResponse(data=tables)


@router.get("/{datasource_id}/tables/{table_name}/columns", response_model=ApiResponse[List[str]])
def list_datasource_columns(datasource_id: int, table_name: str, db: Session = Depends(get_db)):
    datasource = datasource_crud.get(db, id=datasource_id)
    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found")
    try:
        columns = datasource_crud.list_columns(
            db, datasource_id=datasource_id, table_name=table_name
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ApiResponse(data=columns)


@router.post("/agent-datasources", response_model=ApiResponse[AgentDatasourceResponse])
def link_agent_datasource(link_in: AgentDatasourceCreate, db: Session = Depends(get_db)):
    existing = agent_datasource_crud.get_by_agent_and_datasource(
        db, agent_id=link_in.agent_id, datasource_id=link_in.datasource_id
    )
    if existing:
        return ApiResponse(data=AgentDatasourceResponse.model_validate(existing))
    link = agent_datasource_crud.create(db, obj_in=link_in)
    return ApiResponse(data=AgentDatasourceResponse.model_validate(link))


@router.get(
    "/agent-datasources/agent/{agent_id}", response_model=ApiResponse[List[AgentDatasourceResponse]]
)
def list_agent_datasources(agent_id: int, db: Session = Depends(get_db)):
    links = agent_datasource_crud.get_multi_by_agent(db, agent_id=agent_id)
    return ApiResponse(data=[AgentDatasourceResponse.model_validate(link) for link in links])


@router.post("/logical-relations", response_model=ApiResponse[LogicalRelationResponse])
def create_logical_relation(relation_in: LogicalRelationCreate, db: Session = Depends(get_db)):
    relation = logical_relation_crud.create(db, obj_in=relation_in)
    return ApiResponse(data=LogicalRelationResponse.model_validate(relation))


@router.get(
    "/logical-relations/datasource/{datasource_id}",
    response_model=ApiResponse[List[LogicalRelationResponse]],
)
def list_logical_relations(datasource_id: int, db: Session = Depends(get_db)):
    relations = logical_relation_crud.get_multi_by_datasource(db, datasource_id=datasource_id)
    return ApiResponse(data=[LogicalRelationResponse.model_validate(r) for r in relations])
