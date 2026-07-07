from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Agent(Base):
    __tablename__ = "agent"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="智能体名称")
    description = Column(Text, comment="智能体描述")
    avatar = Column(Text, comment="头像URL")
    status = Column(String(50), default="draft", comment="状态：draft-待发布，published-已发布，offline-已下线")
    api_key = Column(String(255), comment="访问 API Key，格式 sk-xxx")
    api_key_enabled = Column(Integer, default=0, comment="API Key 是否启用：0-禁用，1-启用")
    prompt = Column(Text, comment="自定义Prompt配置")
    category = Column(String(100), comment="分类")
    admin_id = Column(BigInteger, comment="管理员ID")
    tags = Column(Text, comment="标签，逗号分隔")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    business_knowledge = relationship("BusinessKnowledge", back_populates="agent", cascade="all, delete-orphan")
    semantic_models = relationship("SemanticModel", back_populates="agent", cascade="all, delete-orphan")
    agent_knowledge = relationship("AgentKnowledge", back_populates="agent", cascade="all, delete-orphan")
    agent_datasources = relationship("AgentDatasource", back_populates="agent", cascade="all, delete-orphan")
    preset_questions = relationship("AgentPresetQuestion", back_populates="agent", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="agent", cascade="all, delete-orphan")


class BusinessKnowledge(Base):
    __tablename__ = "business_knowledge"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    business_term = Column(String(255), nullable=False, comment="业务名词")
    description = Column(Text, comment="描述")
    synonyms = Column(Text, comment="同义词，逗号分隔")
    is_recall = Column(Integer, default=1, comment="是否召回：0-不召回，1-召回")
    agent_id = Column(Integer, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False, comment="关联的智能体ID")
    created_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    embedding_status = Column(String(20), comment="向量化状态")
    error_msg = Column(String(255), comment="操作失败的错误信息")
    is_deleted = Column(Integer, default=0, comment="逻辑删除")
    
    agent = relationship("Agent", back_populates="business_knowledge")
