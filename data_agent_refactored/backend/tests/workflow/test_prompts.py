import json

from app.workflow.prompts.loader import PromptLoader


def test_intent_recognition_prompt_rendering():
    loader = PromptLoader()
    prompt = loader.render(
        "intent-recognition",
        multi_turn="用户: 查一下销售额\nAI: 已查询。",
        latest_query="那上个月的呢",
    )
    assert "查一下销售额" in prompt
    assert "那上个月的呢" in prompt
    assert '"classification"' in prompt


def test_query_enhancement_prompt_rendering():
    loader = PromptLoader()
    prompt = loader.render(
        "query-enhancement",
        current_time_info="2025-11-08 11:11:12",
        evidence="核心用户定义",
        multi_turn="",
        latest_query="上个月核心用户有多少",
    )
    assert "canonical_query" in prompt
    assert "expanded_queries" in prompt


def test_evidence_query_rewrite_prompt_rendering():
    loader = PromptLoader()
    prompt = loader.render(
        "evidence-query-rewrite",
        multi_turn="",
        latest_query="他们呢？",
    )
    assert "standalone_query" in prompt
    assert "他们呢？" in prompt
