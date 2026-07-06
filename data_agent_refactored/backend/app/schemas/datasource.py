from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class DatasourceBase(BaseModel):
    name: str = Field(..., description="数据源名称")
    type: str = Field(..., description="数据源类型")
    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口号")
    database_name: str = Field(..., description="数据库名称")
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    connection_url: Optional[str] = None
    description: Optional[str] = None


class DatasourceCreate(DatasourceBase):
    pass


class DatasourceUpdate(DatasourceBase):
    name: Optional[str] = None
    type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class DatasourceResponse(DatasourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    test_status: str
    create_time: datetime
    update_time: datetime


class AgentDatasourceBase(BaseModel):
    agent_id: int
    datasource_id: int
    is_active: Optional[bool] = False


class AgentDatasourceCreate(AgentDatasourceBase):
    pass


class AgentDatasourceResponse(AgentDatasourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    create_time: datetime
    update_time: datetime


class LogicalRelationBase(BaseModel):
    datasource_id: int
    source_table_name: str
    source_column_name: str
    target_table_name: str
    target_column_name: str
    relation_type: Optional[str] = None
    description: Optional[str] = None


class LogicalRelationCreate(LogicalRelationBase):
    pass


class LogicalRelationResponse(LogicalRelationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool
    created_time: datetime
    updated_time: datetime
