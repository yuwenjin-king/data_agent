from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.schemas.chat import (
    ChatSessionCreate, ChatSessionUpdate, ChatSessionResponse,
    ChatMessageCreate, ChatMessageResponse,
    UserPromptConfigCreate, UserPromptConfigResponse,
    ModelConfigCreate, ModelConfigUpdate, ModelConfigResponse,
    ChatRequest, ChatResponse
)
from app.schemas.common import ApiResponse
from app.services.chat_service import (
    chat_session_crud, chat_message_crud,
    user_prompt_config_crud, model_config_crud
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=ApiResponse[ChatSessionResponse])
def create_session(session_in: ChatSessionCreate, db: Session = Depends(get_db)):
    session = chat_session_crud.create(db, obj_in=session_in)
    return ApiResponse(data=ChatSessionResponse.model_validate(session))


@router.get("/sessions/{session_id}", response_model=ApiResponse[ChatSessionResponse])
def get_session(session_id: str, db: Session = Depends(get_db)):
    session = chat_session_crud.get(db, id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return ApiResponse(data=ChatSessionResponse.model_validate(session))


@router.get("/sessions/agent/{agent_id}", response_model=ApiResponse[List[ChatSessionResponse]])
def list_sessions(agent_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sessions = chat_session_crud.get_multi_by_agent(db, agent_id=agent_id, skip=skip, limit=limit)
    return ApiResponse(data=[ChatSessionResponse.model_validate(s) for s in sessions])


@router.put("/sessions/{session_id}", response_model=ApiResponse[ChatSessionResponse])
def update_session(session_id: str, session_in: ChatSessionUpdate, db: Session = Depends(get_db)):
    session = chat_session_crud.get(db, id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session = chat_session_crud.update(db, db_obj=session, obj_in=session_in)
    return ApiResponse(data=ChatSessionResponse.model_validate(session))


@router.post("/messages", response_model=ApiResponse[ChatMessageResponse])
def create_message(message_in: ChatMessageCreate, db: Session = Depends(get_db)):
    message = chat_message_crud.create(db, obj_in=message_in)
    return ApiResponse(data=ChatMessageResponse.model_validate(message))


@router.get("/messages/session/{session_id}", response_model=ApiResponse[List[ChatMessageResponse]])
def list_messages(session_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    messages = chat_message_crud.get_multi_by_session(db, session_id=session_id, skip=skip, limit=limit)
    return ApiResponse(data=[ChatMessageResponse.model_validate(m) for m in messages])


@router.post("/completions")
async def chat_completion(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = request.session_id
    if not session_id:
        session = chat_session_crud.create(db, obj_in=ChatSessionCreate(
            agent_id=request.agent_id,
            title=request.message[:50] if len(request.message) > 50 else request.message
        ))
        session_id = session.id
    
    user_message = chat_message_crud.create(db, obj_in=ChatMessageCreate(
        session_id=session_id,
        role="user",
        content=request.message
    ))
    
    async def generate():
        yield f"data: {session_id}\n\n"
        yield f"data: Processing your request...\n\n"
        yield f"data: [DONE]\n\n"
    
    if request.stream:
        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        return ApiResponse(data=ChatResponse(
            content="This is a placeholder response. Please implement the actual logic.",
            session_id=session_id
        ))


@router.post("/prompt-configs", response_model=ApiResponse[UserPromptConfigResponse])
def create_prompt_config(config_in: UserPromptConfigCreate, db: Session = Depends(get_db)):
    config = user_prompt_config_crud.create(db, obj_in=config_in)
    return ApiResponse(data=UserPromptConfigResponse.model_validate(config))


@router.get("/prompt-configs", response_model=ApiResponse[List[UserPromptConfigResponse]])
def list_prompt_configs(
    prompt_type: str = None,
    agent_id: int = None,
    db: Session = Depends(get_db)
):
    if prompt_type:
        configs = user_prompt_config_crud.get_multi_by_type(db, prompt_type=prompt_type, agent_id=agent_id)
    else:
        configs = user_prompt_config_crud.get_multi(db)
    return ApiResponse(data=[UserPromptConfigResponse.model_validate(c) for c in configs])


@router.post("/model-configs", response_model=ApiResponse[ModelConfigResponse])
def create_model_config(config_in: ModelConfigCreate, db: Session = Depends(get_db)):
    config = model_config_crud.create(db, obj_in=config_in)
    return ApiResponse(data=ModelConfigResponse.model_validate(config))


@router.get("/model-configs", response_model=ApiResponse[List[ModelConfigResponse]])
def list_model_configs(model_type: str = None, db: Session = Depends(get_db)):
    if model_type:
        configs = model_config_crud.get_multi_by_type(db, model_type=model_type)
    else:
        configs = model_config_crud.get_multi(db)
    return ApiResponse(data=[ModelConfigResponse.model_validate(c) for c in configs])


@router.put("/model-configs/{config_id}", response_model=ApiResponse[ModelConfigResponse])
def update_model_config(config_id: int, config_in: ModelConfigUpdate, db: Session = Depends(get_db)):
    config = model_config_crud.get(db, id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")
    config = model_config_crud.update(db, db_obj=config, obj_in=config_in)
    return ApiResponse(data=ModelConfigResponse.model_validate(config))
