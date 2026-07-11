from typing import Optional

from langchain_core.runnables import RunnableConfig

from app.workflow.llm.client import LLMClient
from app.workflow.prompts.loader import PromptLoader
from app.workflow.sql.schema_builder import format_schema_for_prompt
from app.workflow.state import SqlRetryReason, WorkflowState


def _extract_sql(text: str) -> str:
    text = text.strip()
    # Remove markdown fences if present.
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


async def sql_generate_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    configurable = (config or {}).get("configurable", {})
    llm_client: Optional[LLMClient] = configurable.get("llm_client")

    schema = state.get("table_relation_output")
    evidence = state.get("evidence", "")
    query = state.get("query_enhance_node_output", {}).canonical_query if state.get("query_enhance_node_output") else state.get("input", "")
    dialect = state.get("db_dialect_type", "mysql")
    sql_generate_count = state.get("sql_generate_count", 0)
    retry_reason = state.get("sql_regenerate_reason") or SqlRetryReason()
    previous_sql = state.get("sql_generate_output", "")

    if llm_client is None or schema is None:
        return {
            "sql_generate_output": "",
            "sql_generate_count": sql_generate_count + 1,
        }

    loader = PromptLoader()
    schema_info = format_schema_for_prompt(schema)
    semantic_prompt = state.get("generated_semantic_model_prompt", "")
    full_schema = f"{schema_info}\n\n{semantic_prompt}".strip()

    if retry_reason.kind != "none" and previous_sql:
        prompt = loader.render(
            "sql-error-fixer",
            dialect=dialect,
            error_message=retry_reason.reason,
            schema_info=full_schema,
            execution_description=query,
            error_sql=previous_sql,
            question=state.get("input", ""),
            evidence=evidence,
        )
    else:
        prompt = loader.render(
            "new-sql-generate",
            dialect=dialect,
            schema_info=full_schema,
            evidence=evidence,
            question=state.get("input", ""),
            execution_description=query,
        )

    try:
        response = await llm_client.acomplete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        sql = _extract_sql(response)
    except Exception:
        sql = ""

    return {
        "sql_generate_output": sql,
        "sql_generate_count": sql_generate_count + 1,
        "sql_regenerate_reason": SqlRetryReason(kind="none", reason=""),
    }
