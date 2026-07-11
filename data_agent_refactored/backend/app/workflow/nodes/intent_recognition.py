import json
from typing import Optional

from langchain_core.runnables import RunnableConfig

from app.workflow.llm.client import LLMClient
from app.workflow.prompts.loader import PromptLoader
from app.workflow.state import IntentRecognitionOutput, WorkflowState


# Simple keyword-based fallback when no LLM is available.
DATA_ANALYSIS_KEYWORDS = [
    "查询", "分析", "统计", "列表", "排名", "总和", "平均值", "对比", "多少",
    "最高", "最低", "最大", "最小", "销售", "订单", "用户", "金额", "数量",
]
CHITCHAT_KEYWORDS = [
    "你好", "谢谢", "再见", "嗨", "哈喽", "是谁", "叫什么", "能干什么",
]


def _fallback_intent(query: str) -> IntentRecognitionOutput:
    lowered = query.lower()
    if any(kw in lowered for kw in CHITCHAT_KEYWORDS) and not any(kw in lowered for kw in DATA_ANALYSIS_KEYWORDS):
        return IntentRecognitionOutput(classification="chitchat")
    return IntentRecognitionOutput(classification="data_analysis")


async def intent_recognition_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    configurable = (config or {}).get("configurable", {})
    llm_client: Optional[LLMClient] = configurable.get("llm_client")
    query = state.get("input", "")
    multi_turn = state.get("multi_turn_context", "")

    if llm_client is None:
        output = _fallback_intent(query)
    else:
        loader = PromptLoader()
        prompt = loader.render(
            "intent-recognition",
            multi_turn=multi_turn,
            latest_query=query,
        )
        try:
            response = await llm_client.acomplete(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            parsed = json.loads(response.strip())
            raw_class = parsed.get("classification", "")
            if "闲聊" in raw_class or raw_class == "chitchat":
                classification = "chitchat"
            else:
                classification = "data_analysis"
            output = IntentRecognitionOutput(classification=classification)
        except Exception:
            output = _fallback_intent(query)

    return {"intent_recognition_node_output": output}
