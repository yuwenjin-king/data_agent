import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class WorkflowEvent:
    event: str
    data: Dict[str, Any] = field(default_factory=dict)

    def to_sse(self) -> str:
        payload = json.dumps(self.data, ensure_ascii=False, default=str)
        return f"event: {self.event}\ndata: {payload}\n\n"


def sse_event(event: str, data: Optional[Dict[str, Any]] = None) -> str:
    payload = json.dumps(data or {}, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


def done_event() -> str:
    return sse_event("done")


def error_event(message: str) -> str:
    return sse_event("error", {"message": message})


def node_start_event(node: str) -> str:
    return sse_event("node_start", {"node": node})


def node_chunk_event(node: str, text: str, text_type: str = "text") -> str:
    return sse_event("node_chunk", {"node": node, "text": text, "text_type": text_type})


def node_complete_event(node: str) -> str:
    return sse_event("node_complete", {"node": node})


def sql_event(sql: str) -> str:
    return sse_event("sql", {"sql": sql})


def sql_result_event(result: Any, display_style: Optional[Dict[str, Any]] = None) -> str:
    return sse_event("sql_result", {"result": result, "display_style": display_style or {}})


def session_event(session_id: str, thread_id: Optional[str] = None) -> str:
    return sse_event("session", {"session_id": session_id, "thread_id": thread_id})
