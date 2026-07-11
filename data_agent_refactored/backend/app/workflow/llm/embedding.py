import hashlib
import httpx
from typing import List, Optional
from openai import AsyncOpenAI

from app.models.chat import ModelConfig


class EmbeddingClient:
    """OpenAI-compatible async embedding client with a deterministic dummy fallback."""

    DIMENSION = 1536

    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config
        self.client: Optional[AsyncOpenAI] = None
        if config:
            base_url = config.base_url.rstrip("/")
            if config.embeddings_path:
                base_url = (base_url + "/" + config.embeddings_path.lstrip("/")).rstrip("/")
            http_client = None
            if config.proxy_enabled and config.proxy_host:
                auth = ""
                if config.proxy_username and config.proxy_password:
                    auth = f"{config.proxy_username}:{config.proxy_password}@"
                port = f":{config.proxy_port}" if config.proxy_port else ""
                proxy_url = f"http://{auth}{config.proxy_host}{port}"
                http_client = httpx.AsyncClient(proxy=proxy_url, timeout=httpx.Timeout(600.0))
            self.client = AsyncOpenAI(api_key=config.api_key, base_url=base_url, http_client=http_client)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if self.client is None or self.config is None:
            return [self._dummy_embedding(text) for text in texts]
        response = await self.client.embeddings.create(
            model=self.config.model_name,
            input=texts,
        )
        return [item.embedding for item in response.data]

    async def check_availability(self) -> bool:
        if self.client is None or self.config is None:
            return False
        try:
            await self.embed(["probe"])
            return True
        except Exception:
            return False

    @classmethod
    def _dummy_embedding(cls, text: str) -> List[float]:
        """Deterministic hash-based embedding for offline tests."""
        vec = []
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        for i in range(cls.DIMENSION):
            # Cycle through the 32-byte digest to produce floats in [-1, 1].
            byte = seed[i % len(seed)]
            next_byte = seed[(i + 1) % len(seed)]
            val = ((byte * 256 + next_byte) % 20000) / 10000 - 1
            vec.append(val)
        # Normalize to unit length.
        norm = sum(x * x for x in vec) ** 0.5
        return [x / norm for x in vec] if norm > 0 else vec

    @classmethod
    def dummy(cls) -> "EmbeddingClient":
        return cls(config=None)
