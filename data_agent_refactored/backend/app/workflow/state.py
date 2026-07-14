import json
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

    @staticmethod
    def semantic(reason: str) -> "SqlRetryReason":
        return SqlRetryReason(kind="semantic", reason=reason)

    @staticmethod
    def sql_execute(reason: str) -> "SqlRetryReason":
        return SqlRetryReason(kind="sql_execute", reason=reason)


class ToolParameters(BaseModel):
    instruction: Optional[str] = None
    summary_and_recommendations: Optional[str] = None
    sql_query: Optional[str] = None  # runtime-filled by sql_execute, never set by planner


class ExecutionStep(BaseModel):
    step: int
    tool_to_use: str  # sql_generate | python_generate | report_generator
    tool_parameters: ToolParameters = Field(default_factory=ToolParameters)


class Plan(BaseModel):
    thought_process: str = ""
    execution_plan: List[ExecutionStep] = Field(default_factory=list)

    @staticmethod
    def nl2sql_only_json() -> str:
        """Single-step SQL plan used for nl2sql-only mode and the no-LLM fallback.

        The instruction is intentionally empty so sql_generate falls back to the
        canonical query.
        """
        return json.dumps(
            {
                "thought_process": "nl2sql-only",
                "execution_plan": [
                    {
                        "step": 1,
                        "tool_to_use": "sql_generate",
                        "tool_parameters": {"instruction": ""},
                    }
                ],
            },
            ensure_ascii=False,
        )


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
    plan_validation_status: bool
    plan_validation_error: str
    plan_repair_count: int

    # feasibility gate
    feasibility_assessment_output: str

    # semantic consistency gate
    semantic_consistency_node_output: bool

    # sql generation / execution
    sql_generate_output: str
    sql_generate_count: int
    sql_regenerate_reason: SqlRetryReason
    sql_execute_node_output: Dict[str, Any]
    sql_result_list_memory: List[Dict[str, Any]]

    # python analysis sub-pipeline
    python_generate_node_output: str
    python_execute_node_output: str
    python_is_success: bool
    python_tries_count: int
    python_fallback_mode: bool

    # report / final
    result: str
    error: str

    # internal streaming / metadata
    events: List[WorkflowEvent]
