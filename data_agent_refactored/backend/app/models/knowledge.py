from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SemanticModel(Base):
    __tablename__ = "semantic_model"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(
        Integer,
        ForeignKey("agent.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联的智能体ID",
    )
    datasource_id = Column(Integer, nullable=False, comment="关联的数据源ID")
    table_name = Column(String(255), nullable=False, comment="关联的表名")
    column_name = Column(String(255), nullable=False, default="", comment="数据库中的物理字段名")
    business_name = Column(String(255), nullable=False, default="", comment="业务名/别名")
    synonyms = Column(Text, comment="业务名的同义词")
    business_description = Column(Text, comment="业务描述")
    column_comment = Column(String(255), comment="数据库中的物理字段的原始注释")
    data_type = Column(String(255), nullable=False, default="", comment="物理数据类型")
    status = Column(Integer, default=1, comment="0-停用，1-启用")
    created_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_time = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    agent = relationship("Agent", back_populates="semantic_models")


class AgentKnowledge(Base):
    __tablename__ = "agent_knowledge"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    agent_id = Column(Integer, ForeignKey("agent.id"), nullable=False, comment="关联的智能体ID")
    title = Column(String(255), nullable=False, comment="知识的标题")
    type = Column(
        String(50), nullable=False, comment="知识类型: DOCUMENT-文档, QA-问答, FAQ-常见问题"
    )
    question = Column(Text, comment="问题 (仅当type为QA或FAQ时使用)")
    content = Column(Text, comment="知识内容")
    is_recall = Column(Integer, default=1, comment="业务状态: 1=召回, 0=非召回")
    embedding_status = Column(String(20), comment="向量化状态")
    error_msg = Column(String(255), comment="操作失败的错误信息")
    source_filename = Column(String(500), comment="上传时的原始文件名")
    file_path = Column(String(500), comment="文件在服务器上的物理存储路径")
    file_size = Column(BigInteger, comment="文件大小 (字节)")
    file_type = Column(String(255), comment="文件类型")
    splitter_type = Column(String(50), default="token", comment="分块策略类型")
    created_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_time = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
    is_deleted = Column(Integer, default=0, comment="逻辑删除字段")
    is_resource_cleaned = Column(Integer, default=0, comment="物理资源是否清理")

    agent = relationship("Agent", back_populates="agent_knowledge")


class AgentPresetQuestion(Base):
    __tablename__ = "agent_preset_question"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(
        Integer, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False, comment="智能体ID"
    )
    question = Column(Text, nullable=False, comment="预设问题内容")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_active = Column(Integer, default=0, comment="是否启用：0-禁用，1-启用")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    agent = relationship("Agent", back_populates="preset_questions")
