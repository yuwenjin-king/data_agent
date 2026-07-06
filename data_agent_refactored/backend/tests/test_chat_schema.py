from datetime import datetime

from app.schemas.chat import ChatMessageResponse


class ChatMessageStub:
    id = 1
    session_id = "session-1"
    role = "assistant"
    content = "ok"
    message_type = "text"
    metadata_ = {"sql": "select 1"}
    create_time = datetime(2026, 1, 1)


def test_chat_message_response_reads_reserved_metadata_column():
    response = ChatMessageResponse.model_validate(ChatMessageStub())

    assert response.metadata == {"sql": "select 1"}
    assert response.model_dump(by_alias=True)["metadata"] == {"sql": "select 1"}
