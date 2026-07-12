from typing import Optional

from langchain_core.runnables import RunnableConfig

from app.workflow.llm.client import LLMClient
from app.workflow.prompts.loader import PromptLoader
from app.workflow.sql.schema_builder import format_schema_for_prompt
from app.workflow.state import Plan, WorkflowState


async def planner_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    configurable = (config or {}).get("configurable", {})
    llm_client: Optional[LLMClient] = configurable.get("llm_client")

    is_only_nl2sql = state.get("is_only_nl2sql", False)

    # nl2sql-only mode or no LLM: emit a deterministic single-step SQL plan so
    # the graph still drives sql_generate without calling the LLM.
    if is_only_nl2sql or llm_client is None:
        return {
            "planner_node_output": Plan.nl2sql_only_json(),
            "plan_current_step": 1,
            "plan_validation_status": False,  # forces plan_executor to (re)validate
            "plan_validation_error": "",
        }

    enhance_out = state.get("query_enhance_node_output")
    canonical_query = enhance_out.canonical_query if enhance_out else state.get("input", "")
    schema = state.get("table_relation_output")
    schema_text = format_schema_for_prompt(schema) if schema else ""
    evidence = state.get("evidence", "")
    semantic_model = state.get("generated_semantic_model_prompt", "")
    plan_validation_error = state.get("plan_validation_error", "")

    loader = PromptLoader()
    prompt = loader.render(
        "planner",
        user_question=state.get("input", ""),
        canonical_query=canonical_query,
        schema=schema_text,
        evidence=evidence,
        semantic_model=semantic_model,
        plan_validation_error=plan_validation_error,
    )

    try:
        response = await llm_client.acomplete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        plan_json = response.strip()
    except Exception:
        plan_json = Plan.nl2sql_only_json()

    return {
        "planner_node_output": plan_json,
        "plan_current_step": 1,
        "plan_validation_status": False,  # plan_executor validates before routing
        "plan_validation_error": "",
    }
