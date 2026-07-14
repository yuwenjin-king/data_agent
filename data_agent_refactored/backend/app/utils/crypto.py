import base64
import warnings
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

_dev_key: Optional[str] = None


def _get_fernet() -> Fernet:
    global _dev_key
    key = settings.CRYPTO_KEY.strip()
    if not key:
        if _dev_key is None:
            _dev_key = Fernet.generate_key().decode()
            warnings.warn(
                "CRYPTO_KEY is not set; using a generated development key. "
                "Data encrypted with this key will not be decryptable after restart. "
                "Set CRYPTO_KEY in your .env file.",
                stacklevel=3,
            )
        key = _dev_key
    # Fernet keys must be 32 url-safe base64-encoded bytes
    try:
        decoded = base64.urlsafe_b64decode(key.encode())
        if len(decoded) != 32:
            raise ValueError("Fernet key must be 32 url-safe base64-encoded bytes")
    except Exception as exc:
        raise ValueError(f"Invalid CRYPTO_KEY: {exc}") from exc
    return Fernet(key.encode())


def encrypt(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _get_fernet().decrypt(value.encode()).decode()


def maybe_decrypt(value: Optional[str]) -> Optional[str]:
    """Decrypt a value if it is a valid Fernet token; otherwise return as-is.

    The tolerant fallback keeps the system working for legacy plaintext values
    written before at-rest encryption was introduced, and for test fixtures
    that construct ORM objects with raw strings.
    """
    if not value:
        return value
    try:
        return decrypt(value)
    except (InvalidToken, Exception):
        return value
