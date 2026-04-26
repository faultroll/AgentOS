"""Chatbot App — Basic validation and debugging

Minimal LangGraph app for interactive testing via CLI.
Uses ProcessState with ephemeral memory (no persistence).
"""
import asyncio
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from mcp import ClientSession
from kernel.state import ProcessState


def build_chatbot_app(session: ClientSession):
    """Build the chatbot LangGraph pipeline."""

    async def _execute_mcp_tool(tool_name: str, arguments: dict) -> str:
        try:
            result = await session.call_tool(tool_name, arguments)
            texts = [c.text for c in result.content if hasattr(c, 'text')]
            return "\n".join(texts) if texts else str(result)
        except Exception as e:
            return f"Tool execution error: {e}"

    async def get_model_output(state: ProcessState) -> dict:
        print("\n" + "=" * 60)
        
        # 1. 动态获取由于 Manifest 暴露的 MCP 环境工具
        tools_response = await session.list_tools()
        tools_list = getattr(tools_response, "tools", []) if hasattr(tools_response, "tools") else []
        tools_text = "[可用工具列表]\n"
        for t in tools_list:
            # 兼容 MCP 字典或对象格式
            name = t.name if hasattr(t, "name") else t.get("name")
            desc = t.description if hasattr(t, "description") else t.get("description", "")
            schema = t.inputSchema if hasattr(t, "inputSchema") else t.get("inputSchema", {})
            tools_text += f"- {name}: {desc}\n  参数: {schema}\n"
            
        # 2. 格式化所有历史上下文
        history_text = "\n[上下文历史]\n"
        for m in state["messages"]:
            role = m["role"]
            content = m["content"]
            history_text += f"[{role.upper()}]:\n{content}\n---\n"
            
        copy_payload = f"{tools_text}\n{history_text}"
        print(f"【⚠️ 请复制以下全部内容给网页端的大模型 ⚠️】：\n\n{copy_payload}\n" + "="*60)
        
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(None, lambda: input("请输入模型输出/或人工干预：").strip())
        return {
            "messages": [{"role": "model", "content": raw}],
            "is_finished": "【结束】" in raw,
        }

    def router(state: ProcessState) -> str:
        if state.get("is_finished"):
            return END
        last_msg = state["messages"][-1]["content"]
        if "tools/call" in last_msg:
            return "execute_tool"
        return END

    workflow = StateGraph(ProcessState)
    workflow.add_node("get_model_output", get_model_output)
    workflow.set_entry_point("get_model_output")
    workflow.add_conditional_edges("get_model_output", router)
    return workflow.compile(checkpointer=MemorySaver())
