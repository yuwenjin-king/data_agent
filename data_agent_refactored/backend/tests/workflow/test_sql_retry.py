"""Unit tests for the SQL self-healing router functions (semantic + execute
retry loops) and the global sql_generate_count cap."""

import pytest

from app.workflow.graph import (
    MAX_SQL_GENERATE_COUNT,
    _route_semantic,
    _route_sql_execute,
    _route_sql_generate,
)
from app.workflow.state import SqlRetryReason


def test_route_sql_generate_valid_sql_goes_to_semantic():
    state = {"sql_generate_output": "SELECT 1", "sql_generate_count": 1}
    assert _route_sql_generate(state) == "semantic_consistency"


def test_route_sql_generate_empty_retries_below_cap():
    state = {"sql_generate_output": "", "sql_generate_count": 3}
    assert _route_sql_generate(state) == "sql_generate"


def test_route_sql_generate_empty_at_cap_goes_to_report():
    state = {"sql_generate_output": "", "sql_generate_count": MAX_SQL_GENERATE_COUNT}
    assert _route_sql_generate(state) == "report_generator"


def test_route_sql_generate_cap_goes_to_report_even_with_sql():
    # The global cap applies regardless of SQL content (bounds execute/semantic retries).
    state = {"sql_generate_output": "SELECT 1", "sql_generate_count": MAX_SQL_GENERATE_COUNT}
    assert _route_sql_generate(state) == "report_generator"


def test_route_semantic_pass_goes_to_execute():
    assert _route_semantic({"semantic_consistency_node_output": True}) == "sql_execute"


def test_route_semantic_fail_goes_back_to_generate():
    assert _route_semantic({"semantic_consistency_node_output": False}) == "sql_generate"


def test_route_semantic_defaults_to_pass():
    # Missing key must default to pass (avoid tight loop).
    assert _route_semantic({}) == "sql_execute"


def test_route_sql_execute_success_goes_to_plan_executor():
    assert _route_sql_execute({}) == "plan_executor"


def test_route_sql_execute_fail_goes_back_to_generate():
    state = {"sql_regenerate_reason": SqlRetryReason.sql_execute("boom")}
    assert _route_sql_execute(state) == "sql_generate"


def test_route_sql_execute_semantic_reason_does_not_loop_to_generate():
    # A leftover 'semantic' reason must not trigger an execute-fail retry hop;
    # only kind == 'sql_execute' should.
    state = {"sql_regenerate_reason": SqlRetryReason.semantic("bad")}
    assert _route_sql_execute(state) == "plan_executor"
