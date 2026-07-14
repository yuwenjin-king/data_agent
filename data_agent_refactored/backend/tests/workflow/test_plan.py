"""Unit tests for the plan-driven orchestrator nodes (planner, plan_executor,
feasibility_assessment, semantic_consistency) and their no-LLM fallbacks."""

import json

import pytest

from app.workflow.nodes.feasibility_assessment import feasibility_assessment_node
from app.workflow.nodes.plan_executor import plan_executor_node
from app.workflow.nodes.planner import planner_node
from app.workflow.nodes.semantic_consistency import semantic_consistency_node


def _plan_json(steps):
    return json.dumps({"thought_process": "t", "execution_plan": steps}, ensure_ascii=False)


@pytest.mark.asyncio
async def test_plan_executor_routes_to_first_step():
    plan = _plan_json(
        [
            {"step": 1, "tool_to_use": "sql_generate", "tool_parameters": {"instruction": "do x"}},
            {
                "step": 2,
                "tool_to_use": "report_generator",
                "tool_parameters": {"summary_and_recommendations": "summarize"},
            },
        ]
    )
    out = await plan_executor_node({"planner_node_output": plan, "plan_current_step": 1}, {})
    assert out["plan_validation_status"] is True
    assert out["plan_next_node"] == "sql_generate"


@pytest.mark.asyncio
async def test_plan_executor_routes_to_report_step():
    plan = _plan_json(
        [
            {"step": 1, "tool_to_use": "sql_generate", "tool_parameters": {"instruction": "x"}},
            {
                "step": 2,
                "tool_to_use": "report_generator",
                "tool_parameters": {"summary_and_recommendations": "y"},
            },
        ]
    )
    out = await plan_executor_node({"planner_node_output": plan, "plan_current_step": 2}, {})
    assert out["plan_validation_status"] is True
    assert out["plan_next_node"] == "report_generator"


@pytest.mark.asyncio
async def test_plan_executor_exhausted_routes_to_report():
    plan = _plan_json(
        [{"step": 1, "tool_to_use": "sql_generate", "tool_parameters": {"instruction": "x"}}]
    )
    out = await plan_executor_node({"planner_node_output": plan, "plan_current_step": 2}, {})
    assert out["plan_next_node"] == "report_generator"


@pytest.mark.asyncio
async def test_plan_executor_exhausted_nl2sql_only_routes_to_END():
    plan = _plan_json(
        [{"step": 1, "tool_to_use": "sql_generate", "tool_parameters": {"instruction": "x"}}]
    )
    out = await plan_executor_node(
        {"planner_node_output": plan, "plan_current_step": 2, "is_only_nl2sql": True}, {}
    )
    assert out["plan_next_node"] == "END"


@pytest.mark.asyncio
async def test_plan_executor_rejects_missing_instruction_and_repairs():
    plan = _plan_json(
        [{"step": 1, "tool_to_use": "sql_generate", "tool_parameters": {"instruction": ""}}]
    )
    out = await plan_executor_node({"planner_node_output": plan, "plan_repair_count": 0}, {})
    assert out["plan_validation_status"] is False
    assert out["plan_next_node"] == "planner"
    assert out["plan_repair_count"] == 1


@pytest.mark.asyncio
async def test_plan_executor_rejects_unsupported_tool():
    plan = _plan_json(
        [{"step": 1, "tool_to_use": "drop_table", "tool_parameters": {"instruction": "x"}}]
    )
    out = await plan_executor_node({"planner_node_output": plan}, {})
    assert out["plan_validation_status"] is False
    assert out["plan_next_node"] == "planner"


@pytest.mark.asyncio
async def test_planner_no_llm_fallback_single_sql_step():
    out = await planner_node({"input": "q", "is_only_nl2sql": False}, {"configurable": {}})
    parsed = json.loads(out["planner_node_output"])
    assert len(parsed["execution_plan"]) == 1
    assert parsed["execution_plan"][0]["tool_to_use"] == "sql_generate"
    assert out["plan_current_step"] == 1


@pytest.mark.asyncio
async def test_planner_nl2sql_only_shortcut_without_llm():
    # Even with an LLM present, nl2sql-only mode must skip the LLM call.
    out = await planner_node(
        {"input": "q", "is_only_nl2sql": True},
        {"configurable": {"llm_client": object()}},
    )
    parsed = json.loads(out["planner_node_output"])
    assert parsed["execution_plan"][0]["tool_to_use"] == "sql_generate"


@pytest.mark.asyncio
async def test_feasibility_no_llm_passes_through():
    out = await feasibility_assessment_node({"input": "q"}, {"configurable": {}})
    assert "数据分析" in out["feasibility_assessment_output"]


@pytest.mark.asyncio
async def test_semantic_consistency_no_llm_passes():
    out = await semantic_consistency_node({"sql_generate_output": "SELECT 1"}, {"configurable": {}})
    assert out["semantic_consistency_node_output"] is True
