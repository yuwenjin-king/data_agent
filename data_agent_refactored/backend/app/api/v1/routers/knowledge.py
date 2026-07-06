from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.knowledge import (
    SemanticModelCreate, SemanticModelUpdate, SemanticModelResponse,
    AgentKnowledgeCreate, AgentKnowledgeResponse,
    AgentPresetQuestionCreate, AgentPresetQuestionResponse
)
from app.schemas.common import ApiResponse
from app.services.knowledge_service import semantic_model_crud, agent_knowledge_crud, agent_preset_question_crud

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/semantic-models", response_model=ApiResponse[SemanticModelResponse])
def create_semantic_model(model_in: SemanticModelCreate, db: Session = Depends(get_db)):
    model = semantic_model_crud.create(db, obj_in=model_in)
    return ApiResponse(data=SemanticModelResponse.model_validate(model))


@router.get("/semantic-models/agent/{agent_id}", response_model=ApiResponse[List[SemanticModelResponse]])
def list_semantic_models(agent_id: int, db: Session = Depends(get_db)):
    models = semantic_model_crud.get_multi_by_agent(db, agent_id=agent_id)
    return ApiResponse(data=[SemanticModelResponse.model_validate(m) for m in models])


@router.post("/agent-knowledge", response_model=ApiResponse[AgentKnowledgeResponse])
def create_agent_knowledge(knowledge_in: AgentKnowledgeCreate, db: Session = Depends(get_db)):
    knowledge = agent_knowledge_crud.create(db, obj_in=knowledge_in)
    return ApiResponse(data=AgentKnowledgeResponse.model_validate(knowledge))


@router.get("/agent-knowledge/agent/{agent_id}", response_model=ApiResponse[List[AgentKnowledgeResponse]])
def list_agent_knowledge(agent_id: int, db: Session = Depends(get_db)):
    knowledge_list = agent_knowledge_crud.get_multi_by_agent(db, agent_id=agent_id)
    return ApiResponse(data=[AgentKnowledgeResponse.model_validate(k) for k in knowledge_list])


@router.post("/preset-questions", response_model=ApiResponse[AgentPresetQuestionResponse])
def create_preset_question(question_in: AgentPresetQuestionCreate, db: Session = Depends(get_db)):
    question = agent_preset_question_crud.create(db, obj_in=question_in)
    return ApiResponse(data=AgentPresetQuestionResponse.model_validate(question))


@router.get("/preset-questions/agent/{agent_id}", response_model=ApiResponse[List[AgentPresetQuestionResponse]])
def list_preset_questions(agent_id: int, db: Session = Depends(get_db)):
    questions = agent_preset_question_crud.get_multi_by_agent(db, agent_id=agent_id)
    return ApiResponse(data=[AgentPresetQuestionResponse.model_validate(q) for q in questions])
