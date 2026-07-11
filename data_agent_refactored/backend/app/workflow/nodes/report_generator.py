import json
from typing import Optional

from langchain_core.runnables import RunnableConfig

from app.workflow.llm.client import LLMClient
from app.workflow.prompts.loader import PromptLoader
from app.workflow.state import WorkflowState


async def report_generator_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    configurable = (config or {}).get("configurable", {})
    llm_client: Optional[LLMClient] = configurable.get("llm_client")

    question = state.get("input", "")
    execution_output = state.get("sql_execute_node_output", {})
    result = execution_output.get("result", {})

    if llm_client is None:
        # Fallback: produce a simple markdown summary.
        rows_preview = result.get("rows", [])[:5]
        content = f"### 查询结果\n\n用户问题：{question}\n\n```json\n{json.dumps(rows_preview, ensure_ascii=False, default=str)}\n```"
        return {"result": content}

    loader = PromptLoader()
    analysis_data = json.dumps(execution_output, ensure_ascii=False, default=str)
    prompt = loader.render(
        "report-generator-plain",
        user_requirements_and_plan=f"用户需求：{question}",
        analysis_steps_and_data=analysis_data,
        summary_and_recommendations="请基于上述数据给出简洁的总结与建议。",
        optimization_section="",
    )

    try:
        response = await llm_client.acomplete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.strip()
    except Exception as exc:
        content = f"报告生成失败：{exc}"

    return {"result": content}
