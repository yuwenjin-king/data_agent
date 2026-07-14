from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.chat import ModelConfig
from app.workflow.llm.client import LLMClient
from app.workflow.llm.embedding import EmbeddingClient


@pytest.mark.asyncio
async def test_embedding_client_dummy():
    client = EmbeddingClient.dummy()
    embeddings = await client.embed(["hello", "world"])
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 1536
    # Same input yields same embedding.
    assert embeddings[0] == (await client.embed(["hello"]))[0]


@pytest.mark.asyncio
async def test_llm_client_acomplete(monkeypatch):
    config = ModelConfig(
        provider="openai",
        base_url="https://api.openai.com/v1",
        api_key="sk-test",
        model_name="gpt-4",
        temperature=0.0,
        max_tokens=100,
    )
    client = LLMClient(config)

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello!"
    client.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await client.acomplete([{"role": "user", "content": "hi"}])
    assert result == "Hello!"


@pytest.mark.asyncio
async def test_llm_client_stream(monkeypatch):
    config = ModelConfig(
        provider="openai",
        base_url="https://api.openai.com/v1",
        api_key="sk-test",
        model_name="gpt-4",
        temperature=0.0,
        max_tokens=100,
    )
    client = LLMClient(config)

    async def fake_stream():
        for token in ["He", "llo", "!"]:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = token
            yield chunk

    client.client.chat.completions.create = AsyncMock(return_value=fake_stream())

    chunks = []
    async for token in client.acomplete_stream([{"role": "user", "content": "hi"}]):
        chunks.append(token)
    assert "".join(chunks) == "Hello!"
