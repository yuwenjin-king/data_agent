"""Auth dependencies. require_auth is a no-op unless AUTH_ENABLED is True."""

import secrets
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.agent import Agent
from app.models.user import User
from app.utils.crypto import maybe_decrypt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Resolve the bearer token to a User, or None (no token / invalid)."""
    if not token:
        return None
    username = decode_token(token)
    if not username:
        return None
    return db.query(User).filter(User.username == username, User.is_deleted == 0).first()


def require_auth(user: Optional[User] = Depends(get_current_user)) -> Optional[User]:
    """Enforce auth when AUTH_ENABLED; otherwise a transparent no-op.

    When disabled, returns None so existing open access and tests are unaffected.
    """
    if not settings.AUTH_ENABLED:
        return None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")
    return user


def get_agent_by_api_key(db: Session, *, agent_id: int, api_key: str) -> Optional[Agent]:
    """Resolve an enabled Agent API key bound to the requested agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent or not agent.api_key_enabled or not agent.api_key:
        return None
    stored_key = maybe_decrypt(agent.api_key)
    if not stored_key or not secrets.compare_digest(stored_key, api_key):
        return None
    return agent
