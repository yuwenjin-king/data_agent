from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, BigInteger, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_session"
    
    id = Column(String(36), primary_key=True, comment="会话ID（UUID）")
    agent_id = Column(Integer, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False, comment="智能体ID")
    title = Column(String(255), default="新对话", comment="会话标题")
    status = Column(String(50), default="active", comment="状态：active-活跃，archived-归档，deleted-已删除")
    is_pinned = Column(Boolean, default=False, comment="是否置顶")
    user_id = Column(BigInteger, comment="用户ID")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    agent = relationship("Agent", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_message"
    
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("chat_session.id", ondelete="CASCADE"), nullable=False, comment="会话ID")
    role = Column(String(20), nullable=False, comment="角色：user-用户，assistant-助手，system-系统")
    content = Column(Text, nullable=False, comment="消息内容")
    message_type = Column(String(50), default="text", comment="消息类型：text-文本，sql-SQL查询，result-查询结果，error-错误")
    metadata_ = Column("metadata", JSON, comment="元数据（JSON格式）")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    session = relationship("ChatSession", back_populates="messages")


class UserPromptConfig(Base):
    __tablename__ = "user_prompt_config"
    
    id = Column(String(36), primary_key=True, comment="配置ID（UUID）")
    name = Column(String(255), nullable=False, comment="配置名称")
    prompt_type = Column(String(100), nullable=False, comment="Prompt类型")
    agent_id = Column(Integer, ForeignKey("agent.id"), comment="关联的智能体ID")
    system_prompt = Column(Text, nullable=False, comment="用户自定义系统Prompt内容")
    enabled = Column(Boolean, default=True, comment="是否启用该配置")
    description = Column(Text, comment="配置描述")
    priority = Column(Integer, default=0, comment="配置优先级")
    display_order = Column(Integer, default=0, comment="配置显示顺序")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    creator = Column(String(255), comment="创建者")


class ModelConfig(Base):
    __tablename__ = "model_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(255), nullable=False, comment="厂商标识")
    base_url = Column(String(255), nullable=False, comment="基础URL")
    api_key = Column(String(255), nullable=False, comment="API密钥")
    model_name = Column(String(255), nullable=False, comment="模型名称")
    temperature = Column(Float, default=0.00, comment="温度参数")
    is_active = Column(Boolean, default=False, comment="是否激活")
    max_tokens = Column(Integer, default=2000, comment="输出响应最大令牌数")
    model_type = Column(String(20), nullable=False, default="CHAT", comment="模型类型 (CHAT/EMBEDDING)")
    completions_path = Column(String(255), comment="Chat模型专用路径")
    embeddings_path = Column(String(255), comment="嵌入模型专用路径")
    created_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    is_deleted = Column(Integer, default=0, comment="是否删除")
    proxy_enabled = Column(Boolean, default=False, comment="是否启用代理")
    proxy_host = Column(String(255), comment="代理主机地址")
    proxy_port = Column(Integer, comment="代理端口")
    proxy_username = Column(String(255), comment="代理用户名")
    proxy_password = Column(String(255), comment="代理密码")
