import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from apps.intent_proxy.nodes import architect_node, context_audit_node, memory_recall_node, memory_reflect_node
from kernel.state import create_process

class TestIntentProxyNodes(unittest.IsolatedAsyncioTestCase):
    
    @patch("kernel.drivers.mcp_connect.connect_mcp")
    async def test_memory_recall_node(self, mock_connect):
        """测试记忆检索"""
        mock_session = AsyncMock()
        mock_session.call_tool.return_value = MagicMock(content=[MagicMock(text="Mocked facts")])
        mock_connect.return_value.__aenter__.return_value = mock_session

        state = create_process("test")
        result = await memory_recall_node(state)
        self.assertEqual(result["app_state"]["current_harness_state"], "Active")
        self.assertTrue(len(result["app_state"]["relevant_memory"]) > 0)

    @patch("kernel.drivers.mcp_connect.connect_mcp")
    async def test_memory_reflect_node_trigger(self, mock_connect):
        """测试记忆反思：确保能识别 [PERSIST] 标签并调用 MCP工具"""
        mock_session = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_session

        state = create_process("test")
        state["app_state"] = {}
        state["app_state"]["plan_intelligence"] = {
            "thought": "I should remember this. [PERSIST]: User_Preference | User likes dark mode."
        }
        await memory_reflect_node(state)
        mock_session.call_tool.assert_called_once_with("save_fact", {"title": "User_Preference", "content": "User likes dark mode."})

    async def test_context_audit_node_with_pruning(self):
        """测试上下文审计节点：触发裁剪"""
        state = create_process("query")
        state["messages"] = [{"role": "system", "content": "sys"}] + \
                           [{"role": "user", "content": f"msg {i}"} for i in range(15)]
        
        result = await context_audit_node(state)
        self.assertIn("messages", result)
        self.assertEqual(len(result["messages"]), 10)

if __name__ == "__main__":
    unittest.main()
