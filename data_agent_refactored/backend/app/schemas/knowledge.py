from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SemanticModelBase(BaseModel):
    agent_id: int
    datasource_id: Optional[int] = None
    table_name: str
    column_name: str
    business_name: str
    synonyms: Optional[str] = None
    business_description: Optional[str] = None
    column_comment: Optional[str] = None
    data_type: str
    status: Optional[int] = 1


class SemanticModelCreate(SemanticModelBase):
    pass


class SemanticModelUpdate(BaseModel):
    agent_id: Optional[int] = None
    datasource_id: Optional[int] = None
    table_name: Optional[str] = None
    column_name: Optional[str] = None
    business_name: Optional[str] = None
    synonyms: Optional[str] = None
    business_description: Optional[str] = None
    column_comment: Optional[str] = None
    data_type: Optional[str] = None
    status: Optional[int] = None


class SemanticModelResponse(SemanticModelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_time: datetime
    updated_time: datetime


class SemanticModelBatchImportItem(BaseModel):
    table_name: str
    column_name: str
    business_name: str
    data_type: str
    synonyms: Optional[str] = None
    business_description: Optional[str] = None
    column_comment: Optional[str] = None


class SemanticModelBatchImportRequest(BaseModel):
    agent_id: int
    items: List[SemanticModelBatchImportItem]


class SemanticModelBatchIdsRequest(BaseModel):
    ids: List[int]


class BatchImportResult(BaseModel):
    total: int
    success_count: int
    fail_count: int
    errors: List[str]


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


class AgentKnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    question: Optional[str] = None
    content: Optional[str] = None
    is_recall: Optional[int] = None
    splitter_type: Optional[str] = None


class AgentKnowledgeRecallUpdate(BaseModel):
    is_recall: int


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


class AgentKnowledgeQueryRequest(BaseModel):
    page: int = 1
    page_size: int = 20
    agent_id: Optional[int] = None
    type: Optional[str] = None
    keyword: Optional[str] = None
    embedding_status: Optional[str] = None
    is_recall: Optional[int] = None


class AgentPresetQuestionBase(BaseModel):
    agent_id: int
    question: str
    sort_order: Optional[int] = 0
    is_active: Optional[int] = 0


class AgentPresetQuestionCreate(AgentPresetQuestionBase):
    pass


class AgentPresetQuestionResponse(AgentPresetQuestionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    create_time: datetime
    update_time: datetime
