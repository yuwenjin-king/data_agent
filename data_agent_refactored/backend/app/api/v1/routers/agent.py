import asyncio
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.agent import (
    AgentCreate,
    AgentResponse,
    AgentUpdate,
    ApiKeyResponse,
    BusinessKnowledgeCreate,
    BusinessKnowledgeResponse,
)
from app.schemas.common import ApiResponse
from app.schemas.datasource import InitSchemaRequest
from app.services.agent_service import agent_crud, business_knowledge_crud
from app.services.datasource_service import agent_datasource_crud
from app.workflow.indexing import index_business_knowledge, index_schema_documents
from app.workflow.sql.utils import get_datasource_url_and_dialect

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=ApiResponse[AgentResponse])
def create_agent(agent_in: AgentCreate, db: Session = Depends(get_db)):
    existing = agent_crud.get_by_name(db, name=agent_in.name)
    if existing:
        raise HTTPException(status_code=400, detail="Agent with this name already exists")
    agent = agent_crud.create(db, obj_in=agent_in)
    return ApiResponse(data=AgentResponse.model_validate(agent))


@router.get("/{agent_id}", response_model=ApiResponse[AgentResponse])
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = agent_crud.get(db, id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return ApiResponse(data=AgentResponse.model_validate(agent))


@router.get("", response_model=ApiResponse[List[AgentResponse]])
def list_agents(
    page: int = 1,
    page_size: int = 20,
    status: str = None,
    keyword: str = None,
    db: Session = Depends(get_db)
):
    skip = (page - 1) * page_size
    if keyword:
        agents = agent_crud.search(db, keyword=keyword, skip=skip, limit=page_size)
    elif status:
        agents = agent_crud.get_multi_by_status(db, status=status, skip=skip, limit=page_size)
    else:
        agents = agent_crud.get_multi(db, skip=skip, limit=page_size)
    return ApiResponse(data=[AgentResponse.model_validate(a) for a in agents])


@router.put("/{agent_id}", response_model=ApiResponse[AgentResponse])
def update_agent(agent_id: int, agent_in: AgentUpdate, db: Session = Depends(get_db)):
    agent = agent_crud.get(db, id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent = agent_crud.update(db, db_obj=agent, obj_in=agent_in)
    return ApiResponse(data=AgentResponse.model_validate(agent))


@router.delete("/{agent_id}", response_model=ApiResponse)
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = agent_crud.get(db, id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent_crud.remove(db, id=agent_id)
    return ApiResponse(message="Agent deleted successfully")


@router.post("/{agent_id}/publish", response_model=ApiResponse[AgentResponse])
def publish_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = agent_crud.publish(db, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return ApiResponse(data=AgentResponse.model_validate(agent))


@router.post("/{agent_id}/offline", response_model=ApiResponse[AgentResponse])
def offline_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = agent_crud.offline(db, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return ApiResponse(data=AgentResponse.model_validate(agent))


@router.get("/{agent_id}/api-key", response_model=ApiResponse[ApiKeyResponse])
def get_api_key(agent_id: int, db: Session = Depends(get_db)):
    masked_key, enabled = agent_crud.get_api_key_masked(db, agent_id=agent_id)
    if masked_key is None and enabled is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return ApiResponse(data=ApiKeyResponse(masked_key=masked_key, api_key_enabled=enabled))


@router.post("/{agent_id}/api-key/generate", response_model=ApiResponse[ApiKeyResponse])
def generate_api_key(agent_id: int, db: Session = Depends(get_db)):
    agent, raw_key = agent_crud.generate_api_key(db, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return ApiResponse(data=ApiKeyResponse(api_key=raw_key, api_key_enabled=1))


@router.post("/{agent_id}/api-key/reset", response_model=ApiResponse[ApiKeyResponse])
def reset_api_key(agent_id: int, db: Session = Depends(get_db)):
    agent, raw_key = agent_crud.generate_api_key(db, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return ApiResponse(data=ApiKeyResponse(api_key=raw_key, api_key_enabled=1))


@router.delete("/{agent_id}/api-key", response_model=ApiResponse)
def delete_api_key(agent_id: int, db: Session = Depends(get_db)):
    agent = agent_crud.delete_api_key(db, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return ApiResponse(message="API key deleted successfully")


@router.post("/{agent_id}/api-key/enable", response_model=ApiResponse[ApiKeyResponse])
def set_api_key_enabled(
    agent_id: int,
    enabled: bool = Query(..., description="true to enable, false to disable"),
    db: Session = Depends(get_db)
):
    agent = agent_crud.set_api_key_enabled(db, agent_id=agent_id, enabled=1 if enabled else 0)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    masked_key, _ = agent_crud.get_api_key_masked(db, agent_id=agent_id)
    return ApiResponse(
        data=ApiKeyResponse(masked_key=masked_key, api_key_enabled=agent.api_key_enabled)
    )


@router.post("/{agent_id}/datasources/init-schema", response_model=ApiResponse[List[str]])
def init_agent_schema(
    agent_id: int,
    request: InitSchemaRequest,
    db: Session = Depends(get_db)
):
    agent = agent_crud.get(db, id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    link = agent_datasource_crud.init_schema(
        db, agent_id=agent_id, table_names=request.table_names
    )
    if not link:
        raise HTTPException(status_code=404, detail="No datasource linked to this agent")

    url, _ = get_datasource_url_and_dialect(db, link)
    if url:
        asyncio.run(index_schema_documents(
            db=db,
            datasource_id=link.datasource_id,
            url=url,
            agent_id=agent_id,
            table_names=request.table_names,
        ))

    return ApiResponse(data=request.table_names)


@router.post("/{agent_id}/business-knowledge", response_model=ApiResponse[BusinessKnowledgeResponse])
def create_business_knowledge(
    agent_id: int,
    knowledge_in: BusinessKnowledgeCreate,
    db: Session = Depends(get_db)
):
    agent = agent_crud.get(db, id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    knowledge_in.agent_id = agent_id
    knowledge = business_knowledge_crud.create(db, obj_in=knowledge_in)
    asyncio.run(index_business_knowledge(knowledge))
    return ApiResponse(data=BusinessKnowledgeResponse.model_validate(knowledge))


@router.get("/{agent_id}/business-knowledge", response_model=ApiResponse[List[BusinessKnowledgeResponse]])
def list_business_knowledge(
    agent_id: int,
    db: Session = Depends(get_db)
):
    knowledge_list = business_knowledge_crud.get_multi_by_agent(db, agent_id=agent_id)
    return ApiResponse(data=[BusinessKnowledgeResponse.model_validate(k) for k in knowledge_list])
