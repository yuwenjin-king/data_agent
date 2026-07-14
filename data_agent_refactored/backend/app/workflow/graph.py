from typing import Literal, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from app.core.config import settings
from app.workflow.nodes.evidence_recall import evidence_recall_node
from app.workflow.nodes.feasibility_assessment import feasibility_assessment_node
from app.workflow.nodes.intent_recognition import intent_recognition_node
from app.workflow.nodes.plan_executor import plan_executor_node
from app.workflow.nodes.planner import planner_node
from app.workflow.nodes.python_analyze import python_analyze_node
from app.workflow.nodes.python_execute import python_execute_node
from app.workflow.nodes.python_generate import python_generate_node
from app.workflow.nodes.query_enhance import query_enhance_node
from app.workflow.nodes.report_generator import report_generator_node
from app.workflow.nodes.schema_recall import schema_recall_node
from app.workflow.nodes.semantic_consistency import semantic_consistency_node
from app.workflow.nodes.sql_execute import sql_execute_node
from app.workflow.nodes.sql_generate import sql_generate_node
from app.workflow.nodes.table_relation import table_relation_node
from app.workflow.state import WorkflowState

# Retry caps — every cycle in the graph is bounded by one of these counters.
MAX_SQL_GENERATE_COUNT = 10
MAX_PLAN_REPAIR = 2
MAX_TABLE_RELATION_RETRY = 3


def _route_intent(state: WorkflowState) -> Literal["data_analysis", "chitchat"]:
    output = state.get("intent_recognition_node_output")
    if output and output.classification == "chitchat":
        return "chitchat"
    return "data_analysis"


def _route_table_relation(state: WorkflowState) -> str:
    exception_output = state.get("table_relation_exception_output") or ""
    retry_count = state.get("table_relation_retry_count", 0)
    if exception_output:
        if exception_output.startswith("RETRYABLE:") and retry_count < MAX_TABLE_RELATION_RETRY:
            return "table_relation"
        return END
    # table_relation always returns a SchemaDTO (possibly empty); route forward.
    if state.get("table_relation_output") is not None:
        return "feasibility_assessment"
    return END


def _route_feasibility(state: WorkflowState) -> str:
    output = state.get("feasibility_assessment_output", "") or ""
    # Java marker: 【需求类型】：《数据分析》
    if "数据分析" in output:
        return "planner"
    return END


def _route_plan_executor(state: WorkflowState) -> str:
    if not state.get("plan_validation_status", False):
        if state.get("plan_repair_count", 0) > MAX_PLAN_REPAIR:
            return END
        return "planner"
    next_node = state.get("plan_next_node", END)
    if next_node in ("sql_generate", "python_generate", "report_generator"):
        return next_node
    if next_node == "END":
        return END
    return END


def _route_sql_generate(state: WorkflowState) -> str:
    # Global per-step cap across all SQL retry kinds (empty / semantic / execute).
    if state.get("sql_generate_count", 0) >= MAX_SQL_GENERATE_COUNT:
        return "report_generator"
    sql = (state.get("sql_generate_output") or "").strip()
    if sql == "" or sql.upper() == "END":
        return "sql_generate"  # self-retry (count < cap)
    return "semantic_consistency"


def _route_semantic(state: WorkflowState) -> str:
    passed = state.get("semantic_consistency_node_output", True)
    return "sql_execute" if passed else "sql_generate"


def _route_sql_execute(state: WorkflowState) -> str:
    reason = state.get("sql_regenerate_reason")
    if reason and getattr(reason, "kind", "none") == "sql_execute":
        return "sql_generate"  # execute-fail retry (bounded by sql_generate_count cap)
    return "plan_executor"


def _route_python_execute(state: WorkflowState) -> str:
    if state.get("python_fallback_mode", False):
        return "python_analyze"
    if not state.get("python_is_success", False):
        if state.get("python_tries_count", 0) >= settings.PYTHON_MAX_TRIES:
            return END
        return "python_generate"  # regenerate code (bounded by PYTHON_MAX_TRIES)
    return "python_analyze"


async def chitchat_response(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    return {
        "result": (
            "你好！我是 Data Agent 智能数据助手，可以帮你查询和分析业务数据。"
            '请直接描述你想了解的数据问题，例如："上个月销售额最高的产品是什么？"'
        )
    }


def build_workflow_graph() -> StateGraph:
    graph = StateGraph(WorkflowState)
    graph.add_node("intent_recognition", intent_recognition_node)
    graph.add_node("chitchat", chitchat_response)
    graph.add_node("evidence_recall", evidence_recall_node)
    graph.add_node("query_enhance", query_enhance_node)
    graph.add_node("schema_recall", schema_recall_node)
    graph.add_node("table_relation", table_relation_node)
    graph.add_node("feasibility_assessment", feasibility_assessment_node)
    graph.add_node("planner", planner_node)
    graph.add_node("plan_executor", plan_executor_node)
    graph.add_node("semantic_consistency", semantic_consistency_node)
    graph.add_node("sql_generate", sql_generate_node)
    graph.add_node("sql_execute", sql_execute_node)
    graph.add_node("python_generate", python_generate_node)
    graph.add_node("python_execute", python_execute_node)
    graph.add_node("python_analyze", python_analyze_node)
    graph.add_node("report_generator", report_generator_node)

    graph.add_edge(START, "intent_recognition")
    graph.add_conditional_edges(
        "intent_recognition",
        _route_intent,
        {"chitchat": "chitchat", "data_analysis": "evidence_recall"},
    )
    graph.add_edge("evidence_recall", "query_enhance")
    graph.add_edge("query_enhance", "schema_recall")
    graph.add_edge("schema_recall", "table_relation")

    graph.add_conditional_edges(
        "table_relation",
        _route_table_relation,
        {
            "feasibility_assessment": "feasibility_assessment",
            "table_relation": "table_relation",
            END: END,
        },
    )

    graph.add_conditional_edges(
        "feasibility_assessment",
        _route_feasibility,
        {"planner": "planner", END: END},
    )

    graph.add_edge("planner", "plan_executor")

    graph.add_conditional_edges(
        "plan_executor",
        _route_plan_executor,
        {
            "sql_generate": "sql_generate",
            "python_generate": "python_generate",
            "report_generator": "report_generator",
            "planner": "planner",
            END: END,
        },
    )

    graph.add_conditional_edges(
        "sql_generate",
        _route_sql_generate,
        {
            "sql_generate": "sql_generate",
            "semantic_consistency": "semantic_consistency",
            "report_generator": "report_generator",
        },
    )
    graph.add_conditional_edges(
        "semantic_consistency",
        _route_semantic,
        {"sql_execute": "sql_execute", "sql_generate": "sql_generate"},
    )

    graph.add_conditional_edges(
        "sql_execute",
        _route_sql_execute,
        {"sql_generate": "sql_generate", "plan_executor": "plan_executor"},
    )

    # Python analysis sub-pipeline: plan_executor → python_generate → python_execute
    # → (retry | fallback | analyze) → python_analyze → plan_executor.
    graph.add_edge("python_generate", "python_execute")
    graph.add_conditional_edges(
        "python_execute",
        _route_python_execute,
        {
            "python_analyze": "python_analyze",
            "python_generate": "python_generate",
            END: END,
        },
    )
    graph.add_edge("python_analyze", "plan_executor")

    graph.add_edge("report_generator", END)
    graph.add_edge("chitchat", END)

    return graph.compile()
