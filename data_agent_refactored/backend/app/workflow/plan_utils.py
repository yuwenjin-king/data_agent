"""Helpers for parsing the planner output and reading the current plan step.

Shared by nodes that need the current step's instruction (sql_generate,
semantic_consistency) and by plan_executor for validation/routing.
"""

import json
from typing import Any, Dict

from app.workflow.state import ExecutionStep, Plan


def parse_plan(plan_json: str) -> Plan:
    """Parse a planner output JSON string into a Plan model."""
    data = json.loads(plan_json)
    return Plan.model_validate(data)


def get_current_step(state: Dict[str, Any]) -> ExecutionStep | None:
    """Return the ExecutionStep for plan_current_step, or None if out of range."""
    plan_json = state.get("planner_node_output", "")
    if not plan_json:
        return None
    try:
        plan = parse_plan(plan_json)
    except Exception:
        return None
    idx = state.get("plan_current_step", 1) - 1
    if 0 <= idx < len(plan.execution_plan):
        return plan.execution_plan[idx]
    return None


def get_current_step_instruction(state: Dict[str, Any]) -> str:
    """Return the current step's instruction, or empty string."""
    step = get_current_step(state)
    if step is None:
        return ""
    return step.tool_parameters.instruction or ""
