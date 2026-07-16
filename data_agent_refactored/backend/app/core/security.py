"""Password hashing (bcrypt) and JWT helpers."""

import warnings
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

_dev_secret: Optional[str] = None


def _get_secret_key() -> str:
    """Return the JWT signing key, falling back to a per-process dev key (warned)."""
    global _dev_secret
    key = settings.JWT_SECRET_KEY.strip()
    if not key:
        if _dev_secret is None:
            warnings.warn(
                "JWT_SECRET_KEY is not set; using an ephemeral dev secret. Tokens "
                "will not validate after restart. Set JWT_SECRET_KEY in production.",
                stacklevel=2,
            )
            import secrets

            _dev_secret = secrets.token_urlsafe(48)
        key = _dev_secret
    return key


def hash_password(password: str) -> str:
    # bcrypt has a 72-byte limit; reject longer passwords up front rather than
    # silently truncating.
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > 72:
        raise ValueError("password must be at most 72 bytes")
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, _get_secret_key(), algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    """Return the token's subject, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
