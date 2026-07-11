import json
import uuid
from typing import Any, AsyncIterable, Dict, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chat import ChatMessage, ChatSession
from app.services.chat_service import chat_message_crud, chat_session_crud
from app.workflow.events import (
    done_event,
    error_event,
    node_complete_event,
    node_start_event,
    session_event,
    sql_event,
    sql_result_event,
)
from app.workflow.graph import build_workflow_graph
from app.workflow.llm.client import LLMClient
from app.workflow.llm.embedding import EmbeddingClient
from app.workflow.llm.registry import get_chat_client, get_embedding_client
from app.workflow.vectorstore.store import get_vector_store
from app.schemas.chat import ChatSessionCreate, ChatMessageCreate


def build_multi_turn_context(db: Session, session_id: str, max_turns: int = 10) -> str:
    messages = chat_message_crud.get_multi_by_session(db, session_id=session_id, limit=1000)
    if not messages:
        return ""
    # Keep last N user/assistant pairs.
    relevant = [m for m in messages if m.role in ("user", "assistant")]
    relevant = relevant[-(max_turns * 2):]
    lines = []
    for m in relevant:
        prefix = "用户" if m.role == "user" else "AI"
        lines.append(f"{prefix}: {m.content}")
    return "\n".join(lines)


async def run_chat_workflow(
    db: Session,
    agent_id: int,
    user_message: str,
    session_id: Optional[str] = None,
    thread_id: Optional[str] = None,
) -> AsyncIterable[str]:
    """Run the chat workflow and yield SSE formatted events."""
    thread_id = thread_id or str(uuid.uuid4())

    # Resolve or create session.
    if session_id:
        session = chat_session_crud.get(db, id=session_id)
    else:
        session = None

    if not session:
        session = chat_session_crud.create(
            db,
            obj_in=ChatSessionCreate(agent_id=agent_id, title=user_message[:50] or "新对话"),
        )
        session_id = session.id
    else:
        session_id = session.id

    # Persist user message.
    chat_message_crud.create(
        db,
        obj_in=ChatMessageCreate(
            session_id=session_id,
            role="user",
            content=user_message,
            message_type="text",
        ),
    )

    yield session_event(session_id=session_id, thread_id=thread_id)

    llm_client = get_chat_client(db)
    embedding_client = get_embedding_client(db)
    vector_store = get_vector_store()
    multi_turn = build_multi_turn_context(db, session_id, max_turns=settings.MULTI_TURN_MAX_TURNS)

    initial_state: WorkflowState = {
        "agent_id": agent_id,
        "session_id": session_id,
        "thread_id": thread_id,
        "input": user_message,
        "multi_turn_context": multi_turn,
    }

    config = {
        "configurable": {
            "llm_client": llm_client,
            "embedding_client": embedding_client,
            "vector_store": vector_store,
            "db": db,
        }
    }
    graph = build_workflow_graph()

    final_result = ""
    final_sql = None
    final_execution_result = None
    error_message = None

    try:
        async for chunk in graph.astream(initial_state, config=config, stream_mode="updates"):
            # chunk is a dict like {node_name: partial_state_update}
            for node_name, update in chunk.items():
                yield node_start_event(node=node_name)
                if "result" in update:
                    final_result = update["result"]
                if "sql_generate_output" in update:
                    final_sql = update["sql_generate_output"]
                if "sql_execute_node_output" in update:
                    final_execution_result = update["sql_execute_node_output"]
                if "error" in update:
                    error_message = update["error"]
                yield node_complete_event(node=node_name)
    except Exception as exc:
        error_message = str(exc)
        yield error_event(message=error_message)

    if error_message:
        final_result = final_result or f"处理失败：{error_message}"

    # Stream the final assistant text to the client before persisting.
    yield f"event: message\ndata: {json.dumps({'text': final_result}, ensure_ascii=False)}\n\n"

    # Persist assistant message.
    metadata: Dict[str, Any] = {}
    if final_sql:
        metadata["sql_query"] = final_sql
    if final_execution_result:
        metadata["execution_result"] = final_execution_result
    if error_message:
        metadata["error"] = error_message

    assistant_message = chat_message_crud.create(
        db,
        obj_in=ChatMessageCreate(
            session_id=session_id,
            role="assistant",
            content=final_result,
            message_type="text",
            metadata=metadata,
        ),
    )

    if final_sql:
        yield sql_event(sql=final_sql)
    if final_execution_result:
        yield sql_result_event(result=final_execution_result)

    yield done_event()

    # Return value is consumed by the router; we also embed the assistant message id in the final done for tests.
    # Note: this final event is yielded after done; the caller may ignore it.
    if assistant_message:
        yield f"event: assistant_message\ndata: {json.dumps({'message_id': assistant_message.id}, ensure_ascii=False)}\n\n"
