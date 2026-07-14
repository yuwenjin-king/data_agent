import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.chat import ChatMessage
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionUpdate,
    ModelConfigCreate,
    ModelConfigResponse,
    ModelConfigUpdate,
    UserPromptConfigCreate,
    UserPromptConfigResponse,
)
from app.schemas.common import ApiResponse
from app.services.chat_service import (
    chat_message_crud,
    chat_session_crud,
    model_config_crud,
    user_prompt_config_crud,
)
from app.services.workflow_service import run_chat_workflow

router = APIRouter(prefix="/chat", tags=["chat"])


def _parse_sse_payload(event: str) -> dict:
    """Extract the JSON payload from a single SSE event string."""
    try:
        data = event.split("\ndata: ", 1)[1].split("\n\n")[0]
        return json.loads(data)
    except Exception:
        return {}


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
    messages = chat_message_crud.get_multi_by_session(
        db, session_id=session_id, skip=skip, limit=limit
    )
    return ApiResponse(data=[ChatMessageResponse.model_validate(m) for m in messages])


@router.post("/completions")
async def chat_completion(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = request.session_id

    async def event_stream():
        async for event in run_chat_workflow(
            db=db,
            agent_id=request.agent_id,
            user_message=request.message,
            session_id=session_id,
        ):
            yield event

    if request.stream:
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # Non-streaming: collect all events and return the final result. A run may
    # emit multiple sql / sql_result events (multi-step plan); accumulate them
    # and return the last one in the scalar ChatResponse fields for contract
    # stability. The full list is kept in the persisted message metadata.
    final_content = ""
    final_session_id = session_id
    sql_list: list = []
    result_list: list = []
    async for event in event_stream():
        if event.startswith("event: session"):
            final_session_id = _parse_sse_payload(event).get("session_id", final_session_id)
        elif event.startswith("event: sql\n"):
            sql_list.append(_parse_sse_payload(event).get("sql"))
        elif event.startswith("event: sql_result\n"):
            result_list.append(_parse_sse_payload(event).get("result"))
        elif event.startswith("event: node_complete"):
            pass
        elif event.startswith("event: done"):
            pass

    # For non-streaming, the final assistant content is persisted as a message.
    # Load it from the session to populate content accurately.
    message = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == final_session_id, ChatMessage.role == "assistant")
        .order_by(desc(ChatMessage.id))
        .first()
    )
    if message:
        final_content = message.content

    return ApiResponse(
        data=ChatResponse(
            content=final_content,
            session_id=final_session_id,
            sql_query=sql_list[-1] if sql_list else None,
            execution_result=result_list[-1] if result_list else None,
        )
    )


@router.post("/prompt-configs", response_model=ApiResponse[UserPromptConfigResponse])
def create_prompt_config(config_in: UserPromptConfigCreate, db: Session = Depends(get_db)):
    config = user_prompt_config_crud.create(db, obj_in=config_in)
    return ApiResponse(data=UserPromptConfigResponse.model_validate(config))


@router.get("/prompt-configs", response_model=ApiResponse[List[UserPromptConfigResponse]])
def list_prompt_configs(
    prompt_type: str = None, agent_id: int = None, db: Session = Depends(get_db)
):
    if prompt_type:
        configs = user_prompt_config_crud.get_multi_by_type(
            db, prompt_type=prompt_type, agent_id=agent_id
        )
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
def update_model_config(
    config_id: int, config_in: ModelConfigUpdate, db: Session = Depends(get_db)
):
    config = model_config_crud.get(db, id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")
    config = model_config_crud.update(db, db_obj=config, obj_in=config_in)
    return ApiResponse(data=ModelConfigResponse.model_validate(config))
