from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


from app.workflow.vectorstore.document import VectorDocument


class IntentRecognitionOutput(BaseModel):
    classification: str = Field(..., pattern=r"^(chitchat|data_analysis)$")


class QueryEnhanceOutput(BaseModel):
    canonical_query: str
    expanded_queries: List[str] = Field(default_factory=list)


class EvidenceQueryRewriteOutput(BaseModel):
    standalone_query: str


class ColumnDTO(BaseModel):
    name: str
    data_type: Optional[str] = None
    business_name: Optional[str] = None
    description: Optional[str] = None
    comment: Optional[str] = None
    samples: Optional[List[Any]] = None


class TableDTO(BaseModel):
    name: str
    business_name: Optional[str] = None
    description: Optional[str] = None
    columns: List[ColumnDTO] = Field(default_factory=list)
    primary_key: Optional[List[str]] = None
    foreign_keys: Optional[List[Dict[str, Any]]] = None


class SchemaDTO(BaseModel):
    datasource_id: Optional[int] = None
    dialect: Optional[str] = None
    tables: List[TableDTO] = Field(default_factory=list)


class DisplayStyleBO(BaseModel):
    chart_type: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[List[str]] = None
    title: Optional[str] = None


class SqlRetryReason(BaseModel):
    kind: str = "none"  # none | sql_execute | semantic
    reason: str = ""


class WorkflowEvent(BaseModel):
    event: str
    data: Dict[str, Any] = Field(default_factory=dict)


class WorkflowState(TypedDict, total=False):
    # request / session
    agent_id: int
    session_id: str
    thread_id: str
    input: str
    multi_turn_context: str
    human_review_enabled: bool
    is_only_nl2sql: bool

    # intent
    intent_recognition_node_output: IntentRecognitionOutput

    # evidence / query enhance
    evidence: str
    query_enhance_node_output: QueryEnhanceOutput

    # schema recall
    table_documents_for_schema: List[VectorDocument]
    column_documents_for_schema: List[VectorDocument]

    # table relation / schema assembly
    table_relation_output: SchemaDTO
    table_relation_exception_output: str
    table_relation_retry_count: int
    db_dialect_type: str
    generated_semantic_model_prompt: str

    # planner / executor
    planner_node_output: str  # JSON string of Plan
    plan_current_step: int
    plan_next_node: str

    # sql generation / execution
    sql_generate_output: str
    sql_generate_count: int
    sql_regenerate_reason: SqlRetryReason
    sql_execute_node_output: Dict[str, Any]
    sql_result_list_memory: List[Dict[str, Any]]

    # report / final
    result: str
    error: str

    # internal streaming / metadata
    events: List[WorkflowEvent]
