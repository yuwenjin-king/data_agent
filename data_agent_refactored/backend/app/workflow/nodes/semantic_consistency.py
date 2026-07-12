from typing import Optional

from langchain_core.runnables import RunnableConfig

from app.workflow.llm.client import LLMClient
from app.workflow.plan_utils import get_current_step_instruction
from app.workflow.prompts.loader import PromptLoader
from app.workflow.sql.schema_builder import format_schema_for_prompt
from app.workflow.state import SqlRetryReason, WorkflowState


async def semantic_consistency_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    configurable = (config or {}).get("configurable", {})
    llm_client: Optional[LLMClient] = configurable.get("llm_client")

    sql = (state.get("sql_generate_output") or "").strip()
    schema = state.get("table_relation_output")
    schema_info = format_schema_for_prompt(schema) if schema else ""
    evidence = state.get("evidence", "")
    dialect = state.get("db_dialect_type", "mysql")
    instruction = get_current_step_instruction(state) or state.get("input", "")
    enhance_out = state.get("query_enhance_node_output")
    user_query = enhance_out.canonical_query if enhance_out else state.get("input", "")

    # No LLM: always pass (avoids an empty-SQL <-> semantic-fail tight loop).
    if llm_client is None:
        return {"semantic_consistency_node_output": True}

    loader = PromptLoader()
    prompt = loader.render(
        "semantic-consistency",
        dialect=dialect,
        schema_info=schema_info,
        evidence=evidence,
        execution_description=instruction,
        sql=sql,
        user_query=user_query,
    )

    try:
        response = await llm_client.acomplete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        verdict = response.strip()
    except Exception:
        return {"semantic_consistency_node_output": True}

    if verdict.startswith("不通过"):
        return {
            "semantic_consistency_node_output": False,
            "sql_regenerate_reason": SqlRetryReason.semantic(verdict),
        }
    return {"semantic_consistency_node_output": True}
