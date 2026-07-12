from typing import Optional

from langchain_core.runnables import RunnableConfig

from app.workflow.llm.client import LLMClient
from app.workflow.prompts.loader import PromptLoader
from app.workflow.state import WorkflowState


async def python_analyze_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    configurable = (config or {}).get("configurable", {})
    llm_client: Optional[LLMClient] = configurable.get("llm_client")

    step = state.get("plan_current_step", 1)
    python_output = state.get("python_execute_node_output", "") or ""
    fallback = state.get("python_fallback_mode", False)
    enhance_out = state.get("query_enhance_node_output")
    user_query = enhance_out.canonical_query if enhance_out else state.get("input", "")

    if fallback:
        analysis = "高级分析功能暂时不可用，请稍后重试或简化问题。"
    elif llm_client is None:
        analysis = (
            f"Python 分析输出：\n```\n{python_output}\n```" if python_output else "无分析输出。"
        )
    else:
        loader = PromptLoader()
        prompt = loader.render(
            "python-analyze",
            user_query=user_query,
            python_output=python_output,
        )
        try:
            response = await llm_client.acomplete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            analysis = response.strip()
        except Exception as exc:
            analysis = f"分析生成失败：{exc}"

    # Accumulate per-step analysis; advance the plan cursor back to plan_executor.
    exec_out = dict(state.get("sql_execute_node_output") or {})
    exec_out[f"step_{step}_analysis"] = analysis
    return {"sql_execute_node_output": exec_out, "plan_current_step": step + 1}
