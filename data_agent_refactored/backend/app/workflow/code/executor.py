"""Sandboxed Python code execution for the python_analyze sub-pipeline.

MVP local runner: a subprocess with an AST import guard, a secret-scrubbed
environment, POSIX resource limits (CPU/address-space/nproc), a hard timeout,
and a stdout cap. This is NOT a full sandbox — for production isolation use
the Docker executor (CODE_EXECUTOR_TYPE=docker, currently a stub) or nsjail.
"""
import ast
import os
import subprocess
import sys
import tempfile

from pydantic import BaseModel

from app.core.config import settings

try:  # POSIX-only.
    import resource  # type: ignore
except ImportError:  # pragma: no cover - non-POSIX
    resource = None  # type: ignore


# Modules the generated analysis code is never allowed to touch.
FORBIDDEN_MODULES = {
    "os", "subprocess", "pickle", "socket", "shutil", "pty",
    "multiprocessing", "ctypes", "asyncio",
}

MAX_STDOUT_BYTES = 1 * 1024 * 1024  # 1 MB cap on captured stdout.


class CodeResult(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    exception: str = ""


class CodeSecurityError(Exception):
    """Raised when generated code trips the AST guard."""


def scan_forbidden_imports(code: str) -> None:
    """Reject imports of forbidden modules (deterministic defense-in-depth)."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise CodeSecurityError(f"代码语法错误：{exc}") from exc
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FORBIDDEN_MODULES:
                    raise CodeSecurityError(f"禁止导入模块：{alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in FORBIDDEN_MODULES:
                raise CodeSecurityError(f"禁止导入模块：{node.module}")


def _scrub_env() -> dict:
    """Copy os.environ with secret-bearing vars removed."""
    deny_substrings = ("KEY", "TOKEN", "SECRET", "CREDENTIAL", "PASSWORD", "PASS")
    deny_exact = {"DATABASE_URL", "CRYPTO_KEY"}
    env: dict = {}
    for key, value in os.environ.items():
        if key in deny_exact:
            continue
        if any(sub in key.upper() for sub in deny_substrings):
            continue
        env[key] = value
    env["PATH"] = os.environ.get("PATH", "")
    return env


def _apply_rlimits() -> None:
    """preexec_fn: cap CPU/address-space/nproc in the child only (POSIX)."""
    if resource is None:
        return
    mem_bytes = settings.CODE_MAX_MEMORY_MB * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        if hasattr(resource, "RLIMIT_AS"):
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        if hasattr(resource, "RLIMIT_NPROC"):
            resource.setrlimit(resource.RLIMIT_NPROC, (50, 50))
    except (ValueError, OSError):
        pass


class LocalCodePoolExecutor:
    """Runs generated Python in a subprocess with timeout + rlimits + scrubbed env."""

    def run(self, code: str, stdin: str, timeout_ms: int) -> CodeResult:
        scan_forbidden_imports(code)
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "script.py")
            with open(script_path, "w", encoding="utf-8") as fh:
                fh.write(code)
            try:
                proc = subprocess.run(
                    [sys.executable, "-I", script_path],
                    input=stdin,
                    capture_output=True,
                    text=True,
                    timeout=timeout_ms / 1000,
                    cwd=tmpdir,
                    env=_scrub_env(),
                    preexec_fn=_apply_rlimits if resource is not None else None,
                )
            except subprocess.TimeoutExpired:
                return CodeResult(success=False, exception="代码执行超时")
            stdout = proc.stdout or ""
            if len(stdout.encode("utf-8", "ignore")) > MAX_STDOUT_BYTES:
                stdout = stdout[:MAX_STDOUT_BYTES] + "\n...[stdout truncated]"
            if proc.returncode == 0:
                return CodeResult(success=True, stdout=stdout, stderr=proc.stderr or "")
            return CodeResult(
                success=False,
                stdout=stdout,
                stderr=proc.stderr or "",
                exception=f"进程退出码 {proc.returncode}",
            )


class DockerCodePoolExecutor:
    """Placeholder; real Docker isolation is deferred (Phase C)."""

    def run(self, code: str, stdin: str, timeout_ms: int) -> CodeResult:  # pragma: no cover
        raise NotImplementedError(
            "Docker 代码执行器尚未接入；请设置 CODE_EXECUTOR_TYPE=local。"
        )


def get_code_executor():
    """Factory driven by CODE_EXECUTOR_TYPE (local | docker)."""
    if settings.CODE_EXECUTOR_TYPE == "docker":
        return DockerCodePoolExecutor()
    return LocalCodePoolExecutor()
