from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SemanticModelBase(BaseModel):
    agent_id: int
    datasource_id: int
    table_name: str
    column_name: str
    business_name: str
    synonyms: Optional[str] = None
    business_description: Optional[str] = None
    column_comment: Optional[str] = None
    data_type: str
    status: Optional[bool] = True


class SemanticModelCreate(SemanticModelBase):
    pass


class SemanticModelUpdate(SemanticModelBase):
    agent_id: Optional[int] = None
    datasource_id: Optional[int] = None
    table_name: Optional[str] = None
    column_name: Optional[str] = None
    business_name: Optional[str] = None
    data_type: Optional[str] = None


class SemanticModelResponse(SemanticModelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_time: datetime
    updated_time: datetime


class AgentKnowledgeBase(BaseModel):
    agent_id: int
    title: str
    type: str = Field(..., description="知识类型: DOCUMENT, QA, FAQ")
    question: Optional[str] = None
    content: Optional[str] = None
    is_recall: Optional[int] = 1
    splitter_type: Optional[str] = "token"


class AgentKnowledgeCreate(AgentKnowledgeBase):
    pass


class AgentKnowledgeResponse(AgentKnowledgeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    embedding_status: Optional[str]
    error_msg: Optional[str]
    source_filename: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    file_type: Optional[str]
    created_time: datetime
    updated_time: datetime
    is_deleted: int
    is_resource_cleaned: int


class AgentPresetQuestionBase(BaseModel):
    agent_id: int
    question: str
    sort_order: Optional[int] = 0
    is_active: Optional[bool] = False


class AgentPresetQuestionCreate(AgentPresetQuestionBase):
    pass


class AgentPresetQuestionResponse(AgentPresetQuestionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    create_time: datetime
    update_time: datetime
