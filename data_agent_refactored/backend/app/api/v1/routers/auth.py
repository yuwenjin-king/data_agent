from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth import require_auth
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/status")
def auth_status():
    """Always-open endpoint so the frontend can detect whether auth is required."""
    return ApiResponse(data={"auth_enabled": settings.AUTH_ENABLED})


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username, User.is_deleted == 0).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已禁用")
    token = create_access_token(subject=user.username)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(user: Optional[User] = Depends(require_auth)):
    if user is None:
        # AUTH_ENABLED off — no real session user.
        return ApiResponse(data=None)
    return ApiResponse(
        data={
            "id": user.id,
            "username": user.username,
            "is_superuser": user.is_superuser,
        }
    )
