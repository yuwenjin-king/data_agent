from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Datasource(Base):
    __tablename__ = "datasource"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="数据源名称")
    type = Column(String(50), nullable=False, comment="数据源类型：mysql, postgresql")
    host = Column(String(255), nullable=False, comment="主机地址")
    port = Column(Integer, nullable=False, comment="端口号")
    database_name = Column(String(255), nullable=False, comment="数据库名称")
    username = Column(String(255), nullable=False, comment="用户名")
    password = Column(String(500), nullable=False, comment="密码（加密存储）")
    connection_url = Column(String(1000), comment="完整连接URL")
    status = Column(String(50), default="inactive", comment="状态：active-启用，inactive-禁用")
    test_status = Column(String(50), default="unknown", comment="连接测试状态")
    description = Column(Text, comment="描述")
    creator_id = Column(BigInteger, comment="创建者ID")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    agent_datasources = relationship("AgentDatasource", back_populates="datasource", cascade="all, delete-orphan")
    logical_relations = relationship("LogicalRelation", back_populates="datasource", cascade="all, delete-orphan")


class AgentDatasource(Base):
    __tablename__ = "agent_datasource"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agent.id", ondelete="CASCADE"), nullable=False, comment="智能体ID")
    datasource_id = Column(Integer, ForeignKey("datasource.id", ondelete="CASCADE"), nullable=False, comment="数据源ID")
    is_active = Column(Integer, default=0, comment="是否启用：0-禁用，1-启用")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    agent = relationship("Agent", back_populates="agent_datasources")
    datasource = relationship("Datasource", back_populates="agent_datasources")
    tables = relationship("AgentDatasourceTables", back_populates="agent_datasource", cascade="all, delete-orphan")


class AgentDatasourceTables(Base):
    __tablename__ = "agent_datasource_tables"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_datasource_id = Column(Integer, ForeignKey("agent_datasource.id", ondelete="CASCADE"), nullable=False, comment="智能体数据源ID")
    table_name = Column(String(255), nullable=False, comment="数据表名")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    agent_datasource = relationship("AgentDatasource", back_populates="tables")


class LogicalRelation(Base):
    __tablename__ = "logical_relation"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    datasource_id = Column(Integer, ForeignKey("datasource.id", ondelete="CASCADE"), nullable=False, comment="关联的数据源ID")
    source_table_name = Column(String(100), nullable=False, comment="主表名")
    source_column_name = Column(String(100), nullable=False, comment="主表字段名")
    target_table_name = Column(String(100), nullable=False, comment="关联表名")
    target_column_name = Column(String(100), nullable=False, comment="关联表字段名")
    relation_type = Column(String(20), comment="关系类型: 1:1, 1:N, N:1")
    description = Column(String(500), comment="业务描述")
    is_deleted = Column(Integer, default=0, comment="逻辑删除：0-未删除，1-已删除")
    created_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    datasource = relationship("Datasource", back_populates="logical_relations")
