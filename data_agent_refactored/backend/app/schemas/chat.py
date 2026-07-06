from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatSessionBase(BaseModel):
    id: str
    agent_id: int
    title: Optional[str] = "新对话"
    status: Optional[str] = "active"
    is_pinned: Optional[bool] = False
    user_id: Optional[int] = None


class ChatSessionCreate(BaseModel):
    agent_id: int
    title: Optional[str] = "新对话"
    user_id: Optional[int] = None


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    is_pinned: Optional[bool] = None


class ChatSessionResponse(ChatSessionBase):
    model_config = ConfigDict(from_attributes=True)

    create_time: datetime
    update_time: datetime


class ChatMessageBase(BaseModel):
    session_id: str
    role: str
    content: str
    message_type: Optional[str] = "text"
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metadata_"),
        serialization_alias="metadata",
    )


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageResponse(ChatMessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    create_time: datetime


class UserPromptConfigBase(BaseModel):
    id: str
    name: str
    prompt_type: str
    agent_id: Optional[int] = None
    system_prompt: str
    enabled: Optional[bool] = True
    description: Optional[str] = None
    priority: Optional[int] = 0
    display_order: Optional[int] = 0
    creator: Optional[str] = None


class UserPromptConfigCreate(BaseModel):
    name: str
    prompt_type: str
    agent_id: Optional[int] = None
    system_prompt: str
    enabled: Optional[bool] = True
    description: Optional[str] = None
    priority: Optional[int] = 0
    display_order: Optional[int] = 0
    creator: Optional[str] = None


class UserPromptConfigResponse(UserPromptConfigBase):
    model_config = ConfigDict(from_attributes=True)

    create_time: datetime
    update_time: datetime


class ModelConfigBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: str
    base_url: str
    api_key: str
    model_name: str
    temperature: Optional[float] = 0.00
    is_active: Optional[bool] = False
    max_tokens: Optional[int] = 2000
    model_type: str = "CHAT"
    completions_path: Optional[str] = None
    embeddings_path: Optional[str] = None
    proxy_enabled: Optional[bool] = False
    proxy_host: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None


class ModelConfigCreate(ModelConfigBase):
    pass


class ModelConfigUpdate(ModelConfigBase):
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None


class ModelConfigResponse(ModelConfigBase):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    created_time: datetime
    updated_time: datetime
    is_deleted: int


class ChatRequest(BaseModel):
    agent_id: int
    message: str
    session_id: Optional[str] = None
    stream: Optional[bool] = True


class ChatResponse(BaseModel):
    content: str
    session_id: str
    message_id: Optional[int] = None
    sql_query: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
