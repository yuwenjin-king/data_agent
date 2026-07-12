import asyncio
import json
from typing import Optional

from langchain_core.runnables import RunnableConfig

from app.core.config import settings
from app.workflow.code.executor import CodeResult, CodeSecurityError, get_code_executor
from app.workflow.state import WorkflowState


async def python_execute_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    code = state.get("python_generate_node_output", "")
    tries = state.get("python_tries_count", 0)
    memory = state.get("sql_result_list_memory") or []
    stdin = json.dumps(memory, ensure_ascii=False, default=str)

    executor = get_code_executor()
    # Run the blocking subprocess off the event loop.
    try:
        result: CodeResult = await asyncio.to_thread(
            executor.run, code, stdin, settings.CODE_EXEC_TIMEOUT_MS
        )
    except CodeSecurityError as exc:
        result = CodeResult(success=False, exception=str(exc))

    if result.success:
        return {
            "python_execute_node_output": result.stdout,
            "python_is_success": True,
            "python_fallback_mode": False,
        }

    # Exhausted retries → fallback mode: let python_analyze emit a graceful msg.
    if tries >= settings.PYTHON_MAX_TRIES:
        return {
            "python_execute_node_output": "{}",
            "python_is_success": False,
            "python_fallback_mode": True,
        }

    return {
        "python_execute_node_output": result.exception or result.stderr or "执行失败",
        "python_is_success": False,
    }
