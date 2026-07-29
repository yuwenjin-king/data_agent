import json
import logging
from typing import Any, Dict, Optional

from langchain_core.runnables import RunnableConfig
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import audit_hash, audit_preview
from app.workflow.llm.client import LLMClient
from app.workflow.prompts.loader import PromptLoader
from app.workflow.sql.executor import SqlExecutionError, execute_read_only_sql
from app.workflow.sql.utils import (
    get_datasource_url_and_dialect,
    map_dialect_to_sql_dialect,
    resolve_agent_datasource,
)
from app.workflow.state import SqlRetryReason, WorkflowState

logger = logging.getLogger("app.workflow.sql_execute")


async def sql_execute_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    configurable = (config or {}).get("configurable", {})
    db: Optional[Session] = configurable.get("db")
    llm_client: Optional[LLMClient] = configurable.get("llm_client")

    sql = state.get("sql_generate_output", "")
    agent_id = state.get("agent_id")
    session_id = state.get("session_id")
    thread_id = state.get("thread_id")
    dialect = state.get("db_dialect_type", "mysql")

    if not sql or not sql.strip():
        return {"error": "未能生成有效的 SQL 查询，请检查数据源 schema 是否已配置。"}

    if not db:
        return {"error": "Database session not available"}

    agent_datasource = resolve_agent_datasource(db, agent_id)
    if not agent_datasource:
        return {"error": "No active datasource configured for agent"}

    url, datasource_type = get_datasource_url_and_dialect(db, agent_datasource)
    if not url:
        return {"error": "Failed to build datasource URL"}

    dialect = map_dialect_to_sql_dialect(datasource_type) if datasource_type else dialect
    log_context = {
        "agent_id": agent_id,
        "session_id": session_id,
        "thread_id": thread_id,
        "node": "sql_execute",
        "plan_step": state.get("plan_current_step"),
        "datasource_id": agent_datasource.datasource_id,
        "dialect": dialect,
        "sql_hash": audit_hash(sql),
        "sql_preview": audit_preview(sql),
    }

    try:
        result = execute_read_only_sql(
            url=url,
            sql=sql,
            dialect=dialect,
            timeout=settings.SQL_EXEC_TIMEOUT,
            max_rows=settings.MAX_SQL_ROWS,
        )
    except SqlExecutionError as exc:
        logger.warning("sql.error", extra={**log_context, "reason": str(exc)})
        return {
            "sql_regenerate_reason": SqlRetryReason(kind="sql_execute", reason=str(exc)),
            "sql_execute_node_output": {"error": str(exc)},
        }

    elapsed_seconds = result.get("elapsed_seconds")
    duration_ms = int(float(elapsed_seconds or 0) * 1000)
    logger.info(
        "sql.execute",
        extra={
            **log_context,
            "row_count": result.get("row_count"),
            "elapsed_seconds": elapsed_seconds,
            "duration_ms": duration_ms,
            "truncated": result.get("truncated"),
        },
    )

    # Generate chart config if LLM is available.
    display_style = None
    if llm_client and result["rows"]:
        sample = json.dumps(result["rows"][:3], ensure_ascii=False, default=str)
        loader = PromptLoader()
        prompt = loader.render(
            "data-view-analyze",
            question=state.get("input", ""),
            sample_data=sample,
        )
        try:
            response = await llm_client.acomplete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            display_style = json.loads(response.strip())
        except Exception:
            display_style = None

    execution_output: Dict[str, Any] = {
        "sql": sql,
        "result": result,
    }
    if display_style:
        execution_output["display_style"] = display_style

    # Append (multi-step plans accumulate results) and advance the plan cursor.
    # Reset sql_generate_count so the next plan step starts with a fresh budget.
    memory = list(state.get("sql_result_list_memory") or [])
    memory.append(execution_output)
    return {
        "sql_execute_node_output": execution_output,
        "sql_result_list_memory": memory,
        "plan_current_step": state.get("plan_current_step", 1) + 1,
        "sql_generate_count": 0,
    }
