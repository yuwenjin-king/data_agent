"""Minimal Prometheus-compatible metrics (no extra dependency).

Tracks HTTP request counts by method/status and process uptime, exposed as
Prometheus text via GET /metrics. Cardinality is bounded by using only
method + status code as labels (no raw paths).
"""

import time
from collections import defaultdict
from threading import Lock

_start_time = time.time()
_request_counts: dict[tuple[str, str], int] = defaultdict(int)
_lock = Lock()


def record_request(method: str, status: int) -> None:
    key = (method.upper(), str(status))
    with _lock:
        _request_counts[key] += 1


def snapshot() -> dict[tuple[str, str], int]:
    with _lock:
        return dict(_request_counts)


def uptime_seconds() -> float:
    return time.time() - _start_time


def render_prometheus() -> str:
    """Render the current metrics in Prometheus text exposition format."""
    counts = snapshot()
    lines = [
        "# HELP http_requests_total Total HTTP requests by method and status.",
        "# TYPE http_requests_total counter",
    ]
    for (method, status), count in sorted(counts.items()):
        lines.append(f'http_requests_total{{method="{method}",status="{status}"}} {count}')
    lines.extend(
        [
            "# HELP process_uptime_seconds Seconds since the process started.",
            "# TYPE process_uptime_seconds gauge",
            f"process_uptime_seconds {uptime_seconds():.3f}",
        ]
    )
    return "\n".join(lines) + "\n"
