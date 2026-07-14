from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


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


class DatasourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    host: str
    port: int
    database_name: str
    username: str
    connection_url: Optional[str] = None
    description: Optional[str] = None
    status: str
    test_status: str
    create_time: datetime
    update_time: datetime


class DatasourceTypeResponse(BaseModel):
    type: str
    name: str
    description: Optional[str] = None


class DatasourceTestResponse(BaseModel):
    success: bool
    message: str


class InitSchemaRequest(BaseModel):
    table_names: List[str]


class AgentDatasourceBase(BaseModel):
    agent_id: int
    datasource_id: int
    is_active: Optional[int] = 0


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
    is_deleted: int
    created_time: datetime
    updated_time: datetime
