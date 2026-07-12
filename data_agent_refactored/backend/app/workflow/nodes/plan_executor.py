from typing import Optional

from langchain_core.runnables import RunnableConfig

from app.workflow.plan_utils import parse_plan
from app.workflow.state import WorkflowState


# Supported plan-step tools: sql_generate, python_generate (Phase B), report_generator.
SUPPORTED_TOOLS = {"sql_generate", "python_generate", "report_generator"}


def _validation_failed(state: WorkflowState, message: str) -> WorkflowState:
    return {
        "plan_validation_status": False,
        "plan_validation_error": message,
        "plan_repair_count": state.get("plan_repair_count", 0) + 1,
        "plan_next_node": "planner",
    }


async def plan_executor_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    """Pure routing node: validate the plan and decide the next step's tool.

    Does not call any LLM or perform I/O. Increments plan_current_step is done
    by the executing nodes (sql_execute / python_analyze), not here.
    """
    plan_json = state.get("planner_node_output", "")
    try:
        plan = parse_plan(plan_json)
    except Exception as exc:
        return _validation_failed(state, f"Plan JSON 解析失败：{exc}")

    if not plan.execution_plan:
        return _validation_failed(state, "execution_plan 为空")

    # Structural validation of every step.
    for step in plan.execution_plan:
        tool = step.tool_to_use
        if tool not in SUPPORTED_TOOLS:
            return _validation_failed(state, f"不支持的工具：{tool}")
        params = step.tool_parameters
        if tool == "report_generator":
            if not (params.summary_and_recommendations or "").strip():
                return _validation_failed(state, f"第 {step.step} 步 report_generator 缺少 summary_and_recommendations")
        else:  # sql_generate / python_generate
            if not (params.instruction or "").strip():
                return _validation_failed(state, f"第 {step.step} 步 {tool} 缺少 instruction")

    current = state.get("plan_current_step", 1)
    is_only_nl2sql = state.get("is_only_nl2sql", False)

    # Plan exhausted → finalize.
    if current > len(plan.execution_plan):
        next_node = "END" if is_only_nl2sql else "report_generator"
        return {
            "plan_validation_status": True,
            "plan_next_node": next_node,
            "plan_validation_error": "",
        }

    step = plan.execution_plan[current - 1]
    update: WorkflowState = {
        "plan_validation_status": True,
        "plan_next_node": step.tool_to_use,
        "plan_validation_error": "",
    }
    # Start each python step with a fresh retry budget (python_analyze →
    # plan_executor only re-enters python_generate for a brand-new step, so a
    # reset here is safe and prevents carry-over across python steps).
    if step.tool_to_use == "python_generate":
        update["python_tries_count"] = 0
        update["python_fallback_mode"] = False
        update["python_is_success"] = False
    return update
