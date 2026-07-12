import json
from typing import Optional

from langchain_core.runnables import RunnableConfig

from app.core.config import settings
from app.workflow.llm.client import LLMClient
from app.workflow.plan_utils import get_current_step_instruction
from app.workflow.prompts.loader import PromptLoader
from app.workflow.sql.schema_builder import format_schema_for_prompt
from app.workflow.state import WorkflowState


def _sample_rows(memory) -> str:
    if not memory:
        return "[]"
    last = memory[-1] if isinstance(memory, list) else None
    if not isinstance(last, dict):
        return "[]"
    result = last.get("result") or {}
    rows = result.get("rows", []) if isinstance(result, dict) else []
    return json.dumps(rows[:5], ensure_ascii=False, default=str)


async def python_generate_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    configurable = (config or {}).get("configurable", {})
    llm_client: Optional[LLMClient] = configurable.get("llm_client")

    tries = state.get("python_tries_count", 0)

    # No LLM: emit empty code (the python path is only reached when the planner
    # emits a python step, which it never does in the no-LLM fallback).
    if llm_client is None:
        return {"python_generate_node_output": "", "python_tries_count": tries + 1}

    schema = state.get("table_relation_output")
    schema_text = format_schema_for_prompt(schema) if schema else ""
    instruction = get_current_step_instruction(state) or state.get("input", "")
    prev_code = state.get("python_generate_node_output", "")
    prev_error = ""
    if not state.get("python_is_success", False):
        prev_error = state.get("python_execute_node_output") or ""

    loader = PromptLoader()
    prompt = loader.render(
        "python-generator",
        database_schema=schema_text,
        sample_input=_sample_rows(state.get("sql_result_list_memory")),
        plan_description=instruction,
        python_memory=settings.CODE_MAX_MEMORY_MB,
        python_timeout=settings.CODE_EXEC_TIMEOUT_MS // 1000,
        prev_code=prev_code,
        prev_error=prev_error,
    )

    try:
        response = await llm_client.acomplete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        code = response.strip()
    except Exception:
        code = ""

    return {"python_generate_node_output": code, "python_tries_count": tries + 1}
