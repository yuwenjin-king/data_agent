import json

import pytest


@pytest.mark.asyncio
async def test_chat_completion_streaming_chitchat(client):
    response = client.post(
        "/api/v1/chat/completions",
        json={"agent_id": 1, "message": "你好", "stream": True},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    events = []
    for line in response.iter_lines():
        line = line.decode("utf-8") if isinstance(line, bytes) else line
        if line.startswith("event: "):
            event_name = line[len("event: ") :]
            events.append(event_name)
        elif line.startswith("data: "):
            data = json.loads(line[len("data: ") :])
            events.append((event_name, data))

    event_names = [e for e in events if isinstance(e, str)]
    assert "session" in event_names
    assert "node_start" in event_names
    assert "node_complete" in event_names
    assert "done" in event_names


def test_chat_completion_non_streaming_data_analysis(client):
    response = client.post(
        "/api/v1/chat/completions",
        json={"agent_id": 1, "message": "查询销售额", "stream": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert "data" in payload
    assert "content" in payload["data"]
    assert payload["data"]["session_id"] is not None


def test_chat_completion_creates_session(client):
    response = client.post(
        "/api/v1/chat/completions",
        json={"agent_id": 1, "message": "查询销售额", "stream": False},
    )
    payload = response.json()
    session_id = payload["data"]["session_id"]

    # Verify session exists.
    session_response = client.get(f"/api/v1/chat/sessions/{session_id}")
    assert session_response.status_code == 200
    assert session_response.json()["data"]["id"] == session_id

    # Verify messages were persisted.
    messages_response = client.get(f"/api/v1/chat/messages/session/{session_id}")
    assert messages_response.status_code == 200
    messages = messages_response.json()["data"]
    assert any(m["role"] == "user" for m in messages)
    assert any(m["role"] == "assistant" for m in messages)
