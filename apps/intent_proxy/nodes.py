"""Intent Proxy App — Core Node Logic

All nodes operate on ProcessState. App-specific data lives in
state["app_state"], which the kernel carries but never reads.

App-private keys in app_state:
  - plan_intelligence: dict  (Architect output)
  - relevant_memory: list    (Recalled facts)
  - current_harness_state: str
  - original_model: str
  - final_response: dict
"""
import os
import re
import logging
from typing import Dict, Any
from pathlib import Path

from kernel.state import ProcessState
from kernel.compute.router import call_llm

logger = logging.getLogger(__name__)

# App root directory (resolved relative to this file)
_APP_DIR = Path(__file__).parent
_PROMPTS_DIR = _APP_DIR / "prompts"

# Context limit for architect intent analysis
_CONTEXT_LIMIT = 5


def _load_prompt(filename: str) -> str:
    """Load a prompt from this App's private prompts/ directory."""
    path = _PROMPTS_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ====================== Core Node Logic ======================

async def memory_recall_node(state: ProcessState) -> Dict[str, Any]:
    """[MEMORY - RECALL] Retrieve persistent facts via MCP."""
    logger.info("🧠 [Memory] Retrieving persistent cognition via MCP...")

    last_user_msg = [m["content"] for m in state["messages"] if m["role"] == "user"][-1]

    from kernel.drivers.mcp_connect import connect_mcp
    async with connect_mcp(transport="in_memory") as session:
        recall_resp = await session.call_tool("recall_memory", {"query": last_user_msg})
        facts_text = recall_resp.content[0].text if recall_resp.content else "No relevant memory found."

    # Store in app_state (opaque to kernel)
    app_state = dict(state.get("app_state", {}))
    app_state["relevant_memory"] = [{"file": "Recall_Result", "content": facts_text}]
    app_state["current_harness_state"] = "Active"

    return {"app_state": app_state}


async def architect_node(state: ProcessState) -> Dict[str, Any]:
    """[ROLE A] Intent compilation — injects persistent memory context."""
    logger.info("🛡️ [Architect] Compiling intent...")

    orchestrator_sys_prompt = _load_prompt("orchestrator_instructions.md")

    # Inject persistent cognition
    app_state = dict(state.get("app_state", {}))
    memory_context = "\n### [Persistent Context (Memory)]\n"
    for fact in app_state.get("relevant_memory", []):
        memory_context += f"{fact['content']}\n"

    # Build context window
    clean_context = [m for m in state["messages"] if m["role"] != "system"]
    intent_context = clean_context[-_CONTEXT_LIMIT:] if len(clean_context) > _CONTEXT_LIMIT else clean_context

    meta_directive = {
        "role": "user",
        "content": "请根据当前需求与【Persistent Context】进行意图分析。输出符合协议的 <thought> 和 <blueprint>。"
    }

    full_sys_prompt = f"{orchestrator_sys_prompt}\n{memory_context}"

    intent_analysis_response = await call_llm(
        messages=intent_context + [meta_directive],
        system_prompt=full_sys_prompt,
        app_name="intent-proxy",
    )

    raw_output = intent_analysis_response["choices"][0]["message"]["content"]

    # Parse blueprint
    parsed = {"thought": "", "blueprint": "", "params": {}}
    thought_match = re.search(r'<thought>(.*?)(?:</thought>|$)', raw_output, re.DOTALL | re.IGNORECASE)
    blueprint_match = re.search(r'<blueprint>(.*?)(?:</blueprint>|$)', raw_output, re.DOTALL | re.IGNORECASE)

    if thought_match:
        parsed["thought"] = thought_match.group(1).strip()
    if blueprint_match:
        parsed["blueprint"] = blueprint_match.group(1).strip()

    from config import DEBUG_MODE
    if DEBUG_MODE:
        print(f"\n{'='*60}\n🧠 [Architect Thought]:\n{parsed['thought']}\n{'='*60}")

    app_state["plan_intelligence"] = parsed
    return {"app_state": app_state}


async def context_audit_node(state: ProcessState) -> Dict[str, Any]:
    """[GOVERNANCE] Context audit and pruning."""
    MAX_TURNS = 10
    messages = state["messages"]
    if len(messages) > MAX_TURNS:
        logger.info("✂️ [Audit] Context pruned for protection.")
        pruned = [messages[0]] + messages[-(MAX_TURNS-1):]
        return {"messages": pruned}
    return {}


async def automated_executor_node(state: ProcessState) -> Dict[str, Any]:
    """[ROLE B] Automated execution via Worker."""
    from .workers.router_worker import RouterWorker

    app_state = dict(state.get("app_state", {}))
    worker = RouterWorker()
    response = await worker.run(
        state["messages"],
        original_model=app_state.get("original_model"),
        plan_intelligence=app_state.get("plan_intelligence"),
    )
    app_state["final_response"] = response
    return {"app_state": app_state}


async def memory_reflect_node(state: ProcessState) -> Dict[str, Any]:
    """[MEMORY - REFLECT] Persist new cognition via MCP."""
    app_state = state.get("app_state", {})
    thought = app_state.get("plan_intelligence", {}).get("thought", "")

    if "[PERSIST]:" in thought:
        logger.info("🧠 [Memory] New cognition detected, persisting via MCP...")
        from kernel.drivers.mcp_connect import connect_mcp
        parts = thought.split("[PERSIST]:")
        for part in parts[1:]:
            if "|" in part:
                title, content = part.split("|", 1)
                async with connect_mcp(transport="in_memory") as session:
                    await session.call_tool("save_fact", {
                        "title": title.strip(),
                        "content": content.strip()
                    })
    return {}
