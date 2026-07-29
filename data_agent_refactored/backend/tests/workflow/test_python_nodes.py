"""Tests for the Python analysis sub-pipeline: the local sandbox executor, the
AST guard, the python_execute router, and the python node no-LLM fallbacks."""

import json
import subprocess
from unittest.mock import patch

import pytest
from langgraph.graph import END

from app.core.config import settings
from app.workflow.code.executor import (
    CodeSecurityError,
    DockerCodePoolExecutor,
    LocalCodePoolExecutor,
    scan_forbidden_imports,
)
from app.workflow.graph import _route_python_execute
from app.workflow.nodes.python_analyze import python_analyze_node
from app.workflow.nodes.python_generate import python_generate_node


def test_local_executor_runs_snippet():
    code = (
        "import json, sys\n"
        "data = json.load(sys.stdin)\n"
        "print(json.dumps({'count': len(data), 'total': sum(d.get('x', 0) for d in data)}))\n"
    )
    result = LocalCodePoolExecutor().run(code, json.dumps([{"x": 1}, {"x": 2}, {"x": 3}]), 5000)
    assert result.success
    assert json.loads(result.stdout) == {"count": 3, "total": 6}


def test_local_executor_failure_on_bad_code():
    result = LocalCodePoolExecutor().run("raise ValueError('boom')", "[]", 5000)
    assert not result.success
    assert result.exception


def test_local_executor_timeout():
    result = LocalCodePoolExecutor().run("while True:\n    pass", "[]", 1000)
    assert not result.success
    assert "超时" in result.exception


def test_docker_executor_runs_with_isolation_flags():
    completed = subprocess.CompletedProcess(
        args=["docker"],
        returncode=0,
        stdout='{"ok": true}\n',
        stderr="",
    )
    with patch("app.workflow.code.executor.subprocess.run", return_value=completed) as run:
        result = DockerCodePoolExecutor().run("print('ok')", "[]", 5000)

    assert result.success
    assert result.stdout == '{"ok": true}\n'
    cmd = run.call_args.args[0]
    assert cmd[:4] == ["docker", "run", "--rm", "-i"]
    assert "--network" in cmd
    assert "none" in cmd
    assert "--read-only" in cmd
    assert "--cap-drop" in cmd
    assert "ALL" in cmd
    assert "--security-opt" in cmd
    assert "no-new-privileges" in cmd
    assert "--user" in cmd
    assert "65534:65534" in cmd
    assert "-e" in cmd
    assert "PYTHONDONTWRITEBYTECODE=1" in cmd
    assert settings.DOCKER_IMAGE in cmd
    assert run.call_args.kwargs["input"] == "[]"
    assert set(run.call_args.kwargs["env"]) == {"PATH"}


def test_docker_executor_does_not_require_docker_for_missing_binary():
    with patch(
        "app.workflow.code.executor.subprocess.run",
        side_effect=FileNotFoundError,
    ):
        result = DockerCodePoolExecutor().run("print('ok')", "[]", 1000)

    assert not result.success
    assert "Docker executable not found" in result.exception


def test_ast_guard_rejects_forbidden_imports():
    with pytest.raises(CodeSecurityError):
        scan_forbidden_imports("import os\nos.system('ls')")
    with pytest.raises(CodeSecurityError):
        scan_forbidden_imports("import subprocess")
    with pytest.raises(CodeSecurityError):
        scan_forbidden_imports("from pickle import loads")
    with pytest.raises(CodeSecurityError):
        scan_forbidden_imports("import socket")


def test_ast_guard_allows_safe_imports():
    # Must not raise for the allowed analysis stack.
    scan_forbidden_imports("import json, sys, math\nimport pandas as pd\nimport numpy as np")


def test_route_python_execute_success():
    assert _route_python_execute({"python_is_success": True}) == "python_analyze"


def test_route_python_execute_retry_below_cap():
    assert (
        _route_python_execute({"python_is_success": False, "python_tries_count": 2})
        == "python_generate"
    )


def test_route_python_execute_cap_goes_to_END():
    state = {"python_is_success": False, "python_tries_count": settings.PYTHON_MAX_TRIES}
    assert _route_python_execute(state) == END


def test_route_python_execute_fallback_to_analyze():
    state = {
        "python_is_success": False,
        "python_fallback_mode": True,
        "python_tries_count": 99,
    }
    assert _route_python_execute(state) == "python_analyze"


@pytest.mark.asyncio
async def test_python_generate_no_llm_fallback():
    out = await python_generate_node({"python_tries_count": 0}, {"configurable": {}})
    assert out["python_generate_node_output"] == ""
    assert out["python_tries_count"] == 1


@pytest.mark.asyncio
async def test_python_analyze_no_llm_emits_raw_output():
    out = await python_analyze_node(
        {"plan_current_step": 2, "python_execute_node_output": '{"k": 1}'},
        {"configurable": {}},
    )
    assert out["plan_current_step"] == 3
    analysis = out["sql_execute_node_output"]["step_2_analysis"]
    assert '{"k": 1}' in analysis


@pytest.mark.asyncio
async def test_python_analyze_fallback_message():
    out = await python_analyze_node(
        {"plan_current_step": 1, "python_fallback_mode": True, "python_execute_node_output": "{}"},
        {"configurable": {}},
    )
    assert "不可用" in out["sql_execute_node_output"]["step_1_analysis"]
