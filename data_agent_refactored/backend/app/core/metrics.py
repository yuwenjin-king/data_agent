"""Minimal Prometheus-compatible metrics (no extra dependency).

Tracks HTTP request counts by method/status, workflow operation durations, and
process uptime, exposed as Prometheus text via GET /metrics. Cardinality is
bounded by using only small enum-like labels (no raw paths, IDs, prompts, SQL,
or model names).
"""

import time
from collections import defaultdict
from threading import Lock

_start_time = time.time()
_request_counts: dict[tuple[str, str], int] = defaultdict(int)
_duration_counts: dict[tuple[str, str, str], int] = defaultdict(int)
_duration_sums: dict[tuple[str, str, str], float] = defaultdict(float)
_duration_max: dict[tuple[str, str, str], float] = defaultdict(float)
_lock = Lock()


def record_request(method: str, status: int) -> None:
    key = (method.upper(), str(status))
    with _lock:
        _request_counts[key] += 1


def snapshot() -> dict[tuple[str, str], int]:
    with _lock:
        return dict(_request_counts)


def record_duration_seconds(
    component: str,
    operation: str,
    seconds: float,
    *,
    status: str = "success",
) -> None:
    """Record operation duration using bounded label values."""
    key = (component, operation, status)
    seconds = max(float(seconds), 0.0)
    with _lock:
        _duration_counts[key] += 1
        _duration_sums[key] += seconds
        _duration_max[key] = max(_duration_max[key], seconds)


def duration_snapshot() -> dict[tuple[str, str, str], dict[str, float | int]]:
    with _lock:
        return {
            key: {
                "count": _duration_counts[key],
                "sum": _duration_sums[key],
                "max": _duration_max[key],
            }
            for key in _duration_counts
        }


def uptime_seconds() -> float:
    return time.time() - _start_time


def _render_labels(**labels: str) -> str:
    rendered = []
    for key, value in labels.items():
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        rendered.append(f'{key}="{escaped}"')
    return "{" + ",".join(rendered) + "}"


def render_prometheus() -> str:
    """Render the current metrics in Prometheus text exposition format."""
    counts = snapshot()
    durations = duration_snapshot()
    lines = [
        "# HELP http_requests_total Total HTTP requests by method and status.",
        "# TYPE http_requests_total counter",
    ]
    for (method, status), count in sorted(counts.items()):
        labels = _render_labels(method=method, status=status)
        lines.append(f"http_requests_total{labels} {count}")
    lines.extend(
        [
            "# HELP workflow_operation_duration_seconds_count Workflow operation duration samples.",
            "# TYPE workflow_operation_duration_seconds_count counter",
        ]
    )
    for (component, operation, status), stats in sorted(durations.items()):
        labels = _render_labels(component=component, operation=operation, status=status)
        lines.append(f"workflow_operation_duration_seconds_count{labels} {stats['count']}")
    lines.extend(
        [
            "# HELP workflow_operation_duration_seconds_sum Total workflow operation duration.",
            "# TYPE workflow_operation_duration_seconds_sum counter",
        ]
    )
    for (component, operation, status), stats in sorted(durations.items()):
        labels = _render_labels(component=component, operation=operation, status=status)
        lines.append(f"workflow_operation_duration_seconds_sum{labels} {stats['sum']:.6f}")
    lines.extend(
        [
            "# HELP workflow_operation_duration_seconds_max Max observed workflow operation duration.",
            "# TYPE workflow_operation_duration_seconds_max gauge",
        ]
    )
    for (component, operation, status), stats in sorted(durations.items()):
        labels = _render_labels(component=component, operation=operation, status=status)
        lines.append(f"workflow_operation_duration_seconds_max{labels} {stats['max']:.6f}")
    lines.extend(
        [
            "# HELP process_uptime_seconds Seconds since the process started.",
            "# TYPE process_uptime_seconds gauge",
            f"process_uptime_seconds {uptime_seconds():.3f}",
        ]
    )
    return "\n".join(lines) + "\n"
