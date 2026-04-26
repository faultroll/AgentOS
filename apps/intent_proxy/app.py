"""Intent Proxy App — LangGraph Pipeline

Self-contained App implementing:
  [Recall → Architect → Audit → Execute → Reflect]

All prompts and memory are private to this App.
Communicates with the kernel via ProcessState and kernel syscalls.
"""
from langgraph.graph import StateGraph, END
from kernel.state import ProcessState
from .nodes import (
    architect_node,
    context_audit_node,
    automated_executor_node,
    memory_recall_node,
    memory_reflect_node,
)


def build_app():
    """Build the Intent Proxy LangGraph pipeline."""
    workflow = StateGraph(ProcessState)

    # Register nodes
    workflow.add_node("recall", memory_recall_node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("audit", context_audit_node)
    workflow.add_node("executor", automated_executor_node)
    workflow.add_node("reflect", memory_reflect_node)

    # Execution flow
    workflow.set_entry_point("recall")
    workflow.add_edge("recall", "architect")
    workflow.add_edge("architect", "audit")
    workflow.add_edge("audit", "executor")
    workflow.add_edge("executor", "reflect")
    workflow.add_edge("reflect", END)

    return workflow.compile()


# Global singleton
intent_proxy_app = build_app()
