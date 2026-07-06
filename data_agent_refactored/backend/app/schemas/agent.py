from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class AgentBase(BaseModel):
    name: str = Field(..., description="智能体名称")
    description: Optional[str] = Field(None, description="智能体描述")
    avatar: Optional[str] = Field(None, description="头像URL")
    status: Optional[str] = Field("draft", description="状态")
    api_key: Optional[str] = Field(None, description="API Key")
    api_key_enabled: Optional[bool] = Field(False, description="API Key是否启用")
    prompt: Optional[str] = Field(None, description="自定义Prompt配置")
    category: Optional[str] = Field(None, description="分类")
    tags: Optional[str] = Field(None, description="标签，逗号分隔")


class AgentCreate(AgentBase):
    pass


class AgentUpdate(AgentBase):
    name: Optional[str] = None


class AgentResponse(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    create_time: datetime
    update_time: datetime


class BusinessKnowledgeBase(BaseModel):
    business_term: str = Field(..., description="业务名词")
    description: Optional[str] = None
    synonyms: Optional[str] = None
    is_recall: Optional[int] = 1


class BusinessKnowledgeCreate(BusinessKnowledgeBase):
    agent_id: int


class BusinessKnowledgeUpdate(BusinessKnowledgeBase):
    business_term: Optional[str] = None


class BusinessKnowledgeResponse(BusinessKnowledgeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: int
    created_time: datetime
    updated_time: datetime
    embedding_status: Optional[str]
    error_msg: Optional[str]
    is_deleted: int
