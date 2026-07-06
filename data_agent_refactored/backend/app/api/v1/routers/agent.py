from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, BusinessKnowledgeCreate, BusinessKnowledgeResponse
from app.schemas.common import ApiResponse, PageResponse, PageRequest
from app.services.agent_service import agent_crud, business_knowledge_crud

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
    return ApiResponse(data=BusinessKnowledgeResponse.model_validate(knowledge))


@router.get("/{agent_id}/business-knowledge", response_model=ApiResponse[List[BusinessKnowledgeResponse]])
def list_business_knowledge(
    agent_id: int,
    db: Session = Depends(get_db)
):
    knowledge_list = business_knowledge_crud.get_multi_by_agent(db, agent_id=agent_id)
    return ApiResponse(data=[BusinessKnowledgeResponse.model_validate(k) for k in knowledge_list])
