import asyncio
import json
import logging
import time
from typing import Optional

from langchain_core.runnables import RunnableConfig

from app.core.config import settings
from app.core.metrics import record_duration_seconds
from app.workflow.code.executor import CodeResult, CodeSecurityError, get_code_executor
from app.workflow.state import WorkflowState

logger = logging.getLogger("app.workflow.python_execute")


async def python_execute_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    code = state.get("python_generate_node_output", "")
    tries = state.get("python_tries_count", 0)
    memory = state.get("sql_result_list_memory") or []
    stdin = json.dumps(memory, ensure_ascii=False, default=str)

    executor = get_code_executor()
    started_at = time.perf_counter()
    # Run the blocking subprocess off the event loop.
    try:
        result: CodeResult = await asyncio.to_thread(
            executor.run, code, stdin, settings.CODE_EXEC_TIMEOUT_MS
        )
    except CodeSecurityError as exc:
        result = CodeResult(success=False, exception=str(exc))
    duration_seconds = time.perf_counter() - started_at
    duration_ms = int(duration_seconds * 1000)
    record_duration_seconds(
        "workflow",
        "python_execute",
        duration_seconds,
        status="success" if result.success else "error",
    )

    logger.info(
        "python.execute",
        extra={
            "agent_id": state.get("agent_id"),
            "session_id": state.get("session_id"),
            "thread_id": state.get("thread_id"),
            "node": "python_execute",
            "plan_step": state.get("plan_current_step"),
            "success": result.success,
            "tries": tries,
            "fallback": tries >= settings.PYTHON_MAX_TRIES,
            "duration_ms": duration_ms,
            "executor_type": settings.CODE_EXECUTOR_TYPE,
            "stdout_bytes": len((result.stdout or "").encode("utf-8")),
            "stderr_bytes": len((result.stderr or "").encode("utf-8")),
            "has_exception": bool(result.exception),
        },
    )

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
