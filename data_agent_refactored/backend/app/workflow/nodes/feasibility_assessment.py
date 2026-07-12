from typing import Optional

from langchain_core.runnables import RunnableConfig

from app.workflow.llm.client import LLMClient
from app.workflow.prompts.loader import PromptLoader
from app.workflow.sql.schema_builder import format_schema_for_prompt
from app.workflow.state import WorkflowState


async def feasibility_assessment_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    configurable = (config or {}).get("configurable", {})
    llm_client: Optional[LLMClient] = configurable.get("llm_client")

    enhance_out = state.get("query_enhance_node_output")
    canonical_query = enhance_out.canonical_query if enhance_out else state.get("input", "")
    schema = state.get("table_relation_output")
    schema_text = format_schema_for_prompt(schema) if schema else ""
    evidence = state.get("evidence", "")
    multi_turn = state.get("multi_turn_context", "")

    # No LLM: assume answerable data-analysis (conservative pass-through so the
    # planner/sql path still runs and degrades gracefully).
    if llm_client is None:
        return {
            "feasibility_assessment_output": (
                "【需求类型】：《数据分析》\n【语种类型】：《中文》\n"
                f"【需求内容】：{canonical_query}"
            )
        }

    loader = PromptLoader()
    prompt = loader.render(
        "feasibility-assessment",
        canonical_query=canonical_query,
        recalled_schema=schema_text,
        evidence=evidence,
        multi_turn=multi_turn,
    )

    try:
        response = await llm_client.acomplete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        output = response.strip()
    except Exception:
        # On LLM failure, conservatively allow the request to proceed.
        output = "【需求类型】：《数据分析》"

    return {"feasibility_assessment_output": output}
