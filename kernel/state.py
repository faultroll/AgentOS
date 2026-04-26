"""AgentOS Kernel — Process State (Minimal PCB)

This is the OS-level Process Control Block. It contains ONLY
the fields that the kernel needs to schedule and manage processes.
All application-specific state lives inside the opaque `app_state` dict.
"""
from typing import TypedDict, Annotated, Optional
import uuid


def _merge_messages(left: list, right: list) -> list:
    """Incremental message merge — LangGraph standard pattern."""
    return left + right


class ProcessState(TypedDict):
    """Minimal OS-level PCB — knows nothing about app semantics."""
    # Process identity
    pid: str

    # The universal NL bus — the ONLY channel for natural language
    messages: Annotated[list[dict], _merge_messages]

    # Resource accounting
    token_usage: int

    # Lifecycle
    is_finished: bool

    # Opaque container for app-specific state.
    # The kernel carries it but never reads it.
    app_state: dict


def create_process(query: str, app_name: str = "default") -> ProcessState:
    """Create a new process with a fresh PID."""
    return {
        "pid": f"{app_name}-{uuid.uuid4().hex[:8]}",
        "messages": [{"role": "user", "content": query}],
        "token_usage": 0,
        "is_finished": False,
        "app_state": {},
    }
