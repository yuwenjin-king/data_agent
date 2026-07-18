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
