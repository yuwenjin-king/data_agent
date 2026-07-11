import pytest

from app.schemas.chat import ChatSessionCreate, ChatMessageCreate
from app.services.chat_service import chat_session_crud, chat_message_crud
from app.services.workflow_service import build_multi_turn_context


def test_build_multi_turn_context_includes_recent_messages(db_session):
    session = chat_session_crud.create(db_session, obj_in=ChatSessionCreate(agent_id=1, title="test"))

    for i in range(15):
        chat_message_crud.create(db_session, obj_in=ChatMessageCreate(session_id=session.id, role="user", content=f"question {i}"))
        chat_message_crud.create(db_session, obj_in=ChatMessageCreate(session_id=session.id, role="assistant", content=f"answer {i}"))

    context = build_multi_turn_context(db_session, session.id, max_turns=3)
    # Should only include last 3 turns (6 messages).
    assert "question 12" in context
    assert "answer 14" in context
    assert "question 0" not in context


def test_build_multi_turn_context_empty(db_session):
    session = chat_session_crud.create(db_session, obj_in=ChatSessionCreate(agent_id=1, title="test"))

    context = build_multi_turn_context(db_session, session.id)
    assert context == ""
