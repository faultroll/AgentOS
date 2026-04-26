import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from apps.intent_proxy.app import intent_proxy_app
from kernel.state import create_process

class TestHarnessIntegration(unittest.IsolatedAsyncioTestCase):
    
    @patch("apps.intent_proxy.nodes.call_llm")
    @patch("apps.intent_proxy.workers.router_worker.RouterWorker.run")
    async def test_full_memory_pipeline(self, mock_worker_run, mock_call_llm):
        """测试完整的 Memory-First Harness 管道"""
        
        # 1. 模拟架构师返回 (包含持久化请求)
        mock_call_llm.return_value = {
            "choices": [{"message": {
                "content": "<thought>Test [PERSIST]: Key | Value</thought><blueprint>Action</blueprint>"
            }}]
        }
        
        # 2. 模拟 Worker 返回
        mock_worker_run.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Pipeline works!"}}]
        }
        
        # 3. 模拟存储驱动 MCP
        with patch("kernel.drivers.mcp_connect.connect_mcp") as mock_connect:
            mock_session = AsyncMock()
            mock_connect.return_value.__aenter__.return_value = mock_session
            
            # 执行
            initial_state = create_process("Check memory pipeline", app_name="intent-proxy")
            final_state = await intent_proxy_app.ainvoke(initial_state)
            
            app_state = final_state.get("app_state", {})
            # 验证全链路
            self.assertIn("plan_intelligence", app_state)
            self.assertIn("current_harness_state", app_state) # Recall worked
            self.assertEqual(app_state["final_response"]["choices"][0]["message"]["content"], "Pipeline works!")
            
            # 验证反思持久化是否被触发
            mock_session.call_tool.assert_called_with("save_fact", {"title": "Key", "content": "Value"})

if __name__ == "__main__":
    unittest.main()
