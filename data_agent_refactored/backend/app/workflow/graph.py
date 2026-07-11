from typing import Literal, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from app.workflow.llm.client import LLMClient
from app.workflow.nodes.evidence_recall import evidence_recall_node
from app.workflow.nodes.intent_recognition import intent_recognition_node
from app.workflow.nodes.query_enhance import query_enhance_node
from app.workflow.nodes.report_generator import report_generator_node
from app.workflow.nodes.schema_recall import schema_recall_node
from app.workflow.nodes.sql_execute import sql_execute_node
from app.workflow.nodes.sql_generate import sql_generate_node
from app.workflow.nodes.table_relation import table_relation_node
from app.workflow.state import WorkflowState


def _route_intent(state: WorkflowState) -> Literal["data_analysis", "chitchat"]:
    output = state.get("intent_recognition_node_output")
    if output and output.classification == "chitchat":
        return "chitchat"
    return "data_analysis"


async def chitchat_response(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    return {
        "result": (
            "你好！我是 Data Agent 智能数据助手，可以帮你查询和分析业务数据。"
            "请直接描述你想了解的数据问题，例如：\"上个月销售额最高的产品是什么？\""
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
    graph.add_node("sql_generate", sql_generate_node)
    graph.add_node("sql_execute", sql_execute_node)
    graph.add_node("report_generator", report_generator_node)

    graph.add_edge(START, "intent_recognition")
    graph.add_conditional_edges(
        "intent_recognition",
        _route_intent,
        {
            "chitchat": "chitchat",
            "data_analysis": "evidence_recall",
        },
    )
    graph.add_edge("evidence_recall", "query_enhance")
    graph.add_edge("query_enhance", "schema_recall")
    graph.add_edge("schema_recall", "table_relation")
    graph.add_edge("table_relation", "sql_generate")
    graph.add_edge("sql_generate", "sql_execute")
    graph.add_edge("sql_execute", "report_generator")
    graph.add_edge("report_generator", END)
    graph.add_edge("chitchat", END)

    return graph.compile()
