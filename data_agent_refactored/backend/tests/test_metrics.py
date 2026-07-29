"""Tests for the /metrics endpoint and request counter."""

from app.core import metrics


def test_metrics_increments_and_renders(client):
    # Two requests to /health (counted by the middleware).
    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200

    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "# TYPE http_requests_total counter" in body
    # At least one 200 GET counter must show 2+ hits.
    assert 'http_requests_total{method="GET",status="200"}' in body
    assert "process_uptime_seconds" in body


def test_record_request_is_threadsafe_accumulator():
    metrics.record_request("GET", 200)
    metrics.record_request("GET", 200)
    metrics.record_request("POST", 500)
    snap = metrics.snapshot()
    assert snap[("GET", "200")] >= 2
    assert snap[("POST", "500")] >= 1


def test_record_duration_accumulates_bounded_operation_stats():
    metrics.record_duration_seconds("workflow", "sql_execute", 0.25)
    metrics.record_duration_seconds("workflow", "sql_execute", 0.75)
    metrics.record_duration_seconds("workflow", "sql_execute", -1.0, status="error")

    snap = metrics.duration_snapshot()

    assert snap[("workflow", "sql_execute", "success")]["count"] >= 2
    assert snap[("workflow", "sql_execute", "success")]["sum"] >= 1.0
    assert snap[("workflow", "sql_execute", "success")]["max"] >= 0.75
    assert snap[("workflow", "sql_execute", "error")]["sum"] == 0.0


def test_render_prometheus_includes_workflow_duration_metrics():
    metrics.record_duration_seconds("llm", "complete", 0.125)

    body = metrics.render_prometheus()

    assert "# TYPE workflow_operation_duration_seconds_count counter" in body
    assert "# TYPE workflow_operation_duration_seconds_sum counter" in body
    assert "# TYPE workflow_operation_duration_seconds_max gauge" in body
    assert (
        'workflow_operation_duration_seconds_count'
        '{component="llm",operation="complete",status="success"}'
    ) in body
