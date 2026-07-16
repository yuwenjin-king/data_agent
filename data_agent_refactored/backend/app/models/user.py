from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False, comment="用户名")
    hashed_password = Column(String(255), nullable=False, comment="bcrypt 哈希密码")
    is_active = Column(Integer, default=1, comment="是否启用：0-禁用，1-启用")
    is_superuser = Column(Integer, default=0, comment="是否超级管理员：0-否，1-是")
    created_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_time = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
    is_deleted = Column(Integer, default=0, comment="逻辑删除")
