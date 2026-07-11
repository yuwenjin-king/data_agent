import json
from datetime import datetime
from typing import Optional

from langchain_core.runnables import RunnableConfig

from app.workflow.llm.client import LLMClient
from app.workflow.prompts.loader import PromptLoader
from app.workflow.state import QueryEnhanceOutput, WorkflowState


async def query_enhance_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    configurable = (config or {}).get("configurable", {})
    llm_client: Optional[LLMClient] = configurable.get("llm_client")
    query = state.get("input", "")
    evidence = state.get("evidence", "")
    multi_turn = state.get("multi_turn_context", "")

    if llm_client is None:
        return {"query_enhance_node_output": QueryEnhanceOutput(canonical_query=query)}

    loader = PromptLoader()
    prompt = loader.render(
        "query-enhancement",
        current_time_info=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        evidence=evidence,
        multi_turn=multi_turn,
        latest_query=query,
    )

    try:
        response = await llm_client.acomplete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        parsed = json.loads(response.strip())
        output = QueryEnhanceOutput(
            canonical_query=parsed.get("canonical_query", query),
            expanded_queries=parsed.get("expanded_queries", []),
        )
    except Exception:
        output = QueryEnhanceOutput(canonical_query=query)

    return {"query_enhance_node_output": output}
