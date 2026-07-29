import logging
import time
from typing import Any, AsyncIterable, Dict, List, Optional

import httpx
from openai import AsyncOpenAI

from app.models.chat import ModelConfig
from app.utils.crypto import maybe_decrypt

logger = logging.getLogger("app.workflow.llm")


class LLMClient:
    """OpenAI-compatible async LLM client built from a ModelConfig row."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.model_name = config.model_name
        self.base_url = config.base_url.rstrip("/")
        if config.completions_path:
            # If a custom completions path is provided, treat it as the full chat endpoint base.
            self.base_url = (self.base_url + "/" + config.completions_path.lstrip("/")).rstrip("/")

        http_client = self._build_http_client(config)
        self.client = AsyncOpenAI(
            api_key=maybe_decrypt(config.api_key),
            base_url=self.base_url,
            http_client=http_client,
        )

    @staticmethod
    def _build_http_client(config: ModelConfig) -> Optional[httpx.AsyncClient]:
        if not config.proxy_enabled:
            return None
        proxy_url = None
        if config.proxy_host:
            auth = ""
            if config.proxy_username and config.proxy_password:
                auth = f"{config.proxy_username}:{maybe_decrypt(config.proxy_password)}@"
            port = f":{config.proxy_port}" if config.proxy_port else ""
            proxy_url = f"http://{auth}{config.proxy_host}{port}"
        return httpx.AsyncClient(proxy=proxy_url, timeout=httpx.Timeout(600.0))

    async def acomplete(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        started_at = time.perf_counter()
        try:
            response = await self.client.chat.completions.create(  # type: ignore[call-overload]  # ORM Column config attrs
                model=self.model_name,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature if temperature is not None else self.config.temperature,
                max_tokens=max_tokens if max_tokens is not None else self.config.max_tokens,
                **kwargs,
            )
        except Exception:
            logger.warning(
                "llm.complete.error",
                extra={**self._log_context(), "duration_ms": self._duration_ms(started_at)},
            )
            raise
        logger.info(
            "llm.complete",
            extra={**self._log_context(), "duration_ms": self._duration_ms(started_at)},
        )
        return response.choices[0].message.content or ""

    async def acomplete_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterable[str]:
        started_at = time.perf_counter()
        chunk_count = 0
        try:
            stream = await self.client.chat.completions.create(  # type: ignore[call-overload]  # ORM Column config attrs
                model=self.model_name,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature if temperature is not None else self.config.temperature,
                max_tokens=max_tokens if max_tokens is not None else self.config.max_tokens,
                stream=True,
                **kwargs,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    chunk_count += 1
                    yield delta
        except Exception:
            logger.warning(
                "llm.stream.error",
                extra={
                    **self._log_context(),
                    "duration_ms": self._duration_ms(started_at),
                    "chunk_count": chunk_count,
                },
            )
            raise
        logger.info(
            "llm.stream",
            extra={
                **self._log_context(),
                "duration_ms": self._duration_ms(started_at),
                "chunk_count": chunk_count,
            },
        )

    async def check_availability(self) -> bool:
        try:
            # Try a tiny completion as a health probe.
            await self.acomplete(
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
                temperature=0.0,
            )
            return True
        except Exception:
            return False

    @property
    def provider(self) -> str:
        return self.config.provider  # type: ignore[return-value]  # ORM Column[str]

    def _log_context(self) -> dict[str, Any]:
        return {
            "model_config_id": self.config.id,
            "provider": self.provider,
            "model": self.model_name,
            "operation": "chat.completions",
        }

    @staticmethod
    def _duration_ms(started_at: float) -> int:
        return int((time.perf_counter() - started_at) * 1000)
