import re
import time
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


class SqlExecutionError(Exception):
    pass


class SqlNotAllowedError(SqlExecutionError):
    pass


# DML/DDL keywords that are not allowed in read-only mode.
FORBIDDEN_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter", "create", "truncate",
    "grant", "revoke", "execute", "call", "merge", "replace", "upsert",
    "copy", "load", "attach", "detach",
]


def _validate_read_only(sql: str) -> None:
    """Ensure the SQL is a SELECT statement."""
    cleaned = re.sub(r"--[^\n]*|/\*.*?\*/", " ", sql, flags=re.DOTALL)
    first_token = cleaned.strip().split(None, 1)[0].lower()
    if first_token != "select":
        raise SqlNotAllowedError(f"Only SELECT statements are allowed, got: {first_token}")
    lowered = cleaned.lower()
    for keyword in FORBIDDEN_KEYWORDS:
        # Use word boundary to reduce false positives.
        if re.search(rf"\b{keyword}\b", lowered):
            raise SqlNotAllowedError(f"Forbidden keyword detected: {keyword}")


def _add_limit_if_missing(sql: str, max_rows: int) -> str:
    """Append LIMIT if the query does not already contain one."""
    # Simple heuristic: check for LIMIT or FETCH at end of statement.
    stripped = sql.strip().rstrip(";")
    lowered = stripped.lower()
    if "limit" in lowered or "fetch" in lowered:
        return stripped
    return f"{stripped} LIMIT {max_rows}"


def execute_read_only_sql(
    url: str,
    sql: str,
    dialect: Optional[str] = None,
    timeout: int = 30,
    max_rows: int = 500,
) -> Dict[str, Any]:
    """Execute a read-only SQL query against an agent datasource.

    Returns a dict with keys: columns, rows, row_count, truncated.
    """
    _validate_read_only(sql)
    bounded_sql = _add_limit_if_missing(sql, max_rows + 1)

    connect_args = {}
    if dialect not in ("sqlite",):
        connect_args["connect_timeout"] = timeout
    engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    start = time.time()
    try:
        with engine.connect() as conn:
            # Best-effort statement timeout.
            if dialect in ("postgresql", "mysql"):
                timeout_stmt = "SET statement_timeout = :timeout" if dialect == "postgresql" else "SET SESSION MAX_EXECUTION_TIME=:timeout"
                try:
                    conn.execute(text(timeout_stmt), {"timeout": timeout * 1000})
                except SQLAlchemyError:
                    pass  # Some drivers may not support it.

            result = conn.execute(text(bounded_sql))
            columns = list(result.keys())
            rows = []
            truncated = False
            for idx, row in enumerate(result):
                if idx >= max_rows:
                    truncated = True
                    break
                rows.append(dict(row._mapping))
    except SQLAlchemyError as exc:
        raise SqlExecutionError(str(exc)) from exc
    finally:
        engine.dispose()

    elapsed = time.time() - start
    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
        "elapsed_seconds": round(elapsed, 3),
    }
