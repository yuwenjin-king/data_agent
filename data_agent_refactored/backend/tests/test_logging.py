"""Tests for the JSON structured logging setup."""

import json
import logging
import sys

from app.core.logging import JsonFormatter, audit_hash, audit_preview, setup_logging


def test_json_formatter_emits_structured_fields():
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="workflow.start",
        args=None,
        exc_info=None,
    )
    record.agent_id = 7
    record.session_id = "s-123"
    payload = json.loads(JsonFormatter().format(record))

    assert payload["msg"] == "workflow.start"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["agent_id"] == 7
    assert payload["session_id"] == "s-123"
    assert "ts" in payload


def test_json_formatter_includes_exception():
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord(
            "app.test", logging.ERROR, __file__, 1, "workflow.error", None, sys.exc_info()
        )
    payload = json.loads(JsonFormatter().format(record))
    assert "exc" in payload
    assert "ValueError" in payload["exc"]


def test_extra_fields_surface_in_captured_records(caplog):
    logger = logging.getLogger("app.test.extra")
    with caplog.at_level(logging.INFO, logger="app.test.extra"):
        logger.info("sql.execute", extra={"row_count": 5, "elapsed_seconds": 0.12})
    record = next(r for r in caplog.records if r.msg == "sql.execute")
    assert record.row_count == 5
    assert record.elapsed_seconds == 0.12
    # And the JSON rendering surfaces them too.
    payload = json.loads(JsonFormatter().format(record))
    assert payload["row_count"] == 5


def test_audit_hash_returns_stable_short_digest():
    assert audit_hash("SELECT * FROM orders") == audit_hash("SELECT * FROM orders")
    assert audit_hash("SELECT * FROM orders") != audit_hash("SELECT * FROM users")
    assert len(audit_hash("SELECT * FROM orders")) == 16
    assert audit_hash("value", length=8) == audit_hash("value")[:8]


def test_audit_preview_collapses_and_limits_text():
    sql = """
        SELECT *
        FROM orders
        WHERE status = 'paid'
    """

    assert audit_preview(sql) == "SELECT * FROM orders WHERE status = 'paid'"
    assert audit_preview(sql, limit=15) == "SELECT * FROM o"
    assert audit_preview(None) == ""


def test_json_formatter_emits_audit_context_fields():
    record = logging.LogRecord(
        name="app.workflow.sql_execute",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="sql.execute",
        args=None,
        exc_info=None,
    )
    record.agent_id = 7
    record.thread_id = "thread-1"
    record.node = "sql_execute"
    record.sql_hash = audit_hash("select 1")
    record.duration_ms = 12
    payload = json.loads(JsonFormatter().format(record))

    assert payload["agent_id"] == 7
    assert payload["thread_id"] == "thread-1"
    assert payload["node"] == "sql_execute"
    assert payload["sql_hash"] == audit_hash("select 1")
    assert payload["duration_ms"] == 12


def test_setup_logging_configures_root():
    setup_logging("WARNING")
    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert any(isinstance(h.formatter, JsonFormatter) for h in root.handlers)
    # Restore default logging for the rest of the suite.
    setup_logging("INFO")
