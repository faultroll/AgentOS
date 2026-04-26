import unittest
import builtins
import httpx
from fastapi.testclient import TestClient
from rootfs.applets.gateway import app
from unittest.mock import patch, AsyncMock, MagicMock

class TestGateway(unittest.IsolatedAsyncioTestCase):
    """
    AgentOS Gateway 统一测试套件。
    遵循双向盲从原则：验证网关与内核 Router 的协议连通性，不依赖任何外部 apps/ 代码。
    """
    
    def setUp(self):
        self.client = TestClient(app)
        # 注入内核调度器 Mock (Rootfs 运行时的物理前置条件)
        mock_scheduler = MagicMock()
        mock_scheduler.select_model.return_value = ["test-kernel-model"]
        mock_scheduler._models = {"test-kernel-model": MagicMock()}
        builtins._os_scheduler = mock_scheduler

    def test_gateway_get_models(self):
        """测试 /v1/models 是否正确映射内核模型（而非物理 App）"""
        response = self.client.get("/v1/models")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"][0]["id"], "test-kernel-model")

    @patch("rootfs.applets.gateway.call_llm", new_callable=AsyncMock)
    async def test_gateway_forward_logic(self, mock_call_llm):
        """测试网关是否将请求正确转发至内核 Router，并携带正确的 Telemetry 标签"""
        
        # 1. 模拟内核返回
        mock_call_llm.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "OS Level Response"}}]
        }

        # 2. 模拟外部请求 (带 App Hijack 标签)
        payload = {
            "model": "game-engine:gpt-4o",
            "messages": [{"role": "user", "content": "Action: Move North"}]
        }
        
        # 3. 逻辑验证
        response = self.client.post("/v1/chat/completions", json=payload)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["choices"][0]["message"]["content"], "OS Level Response")
        
        # 4. 盲目性断言
        # 网关应能解析出 'game-engine' 标签，但不应尝试去物理加载它。
        # 它仅仅将这个标签作为 app_name 传给内核进行算力审计。
        mock_call_llm.assert_called_once()
        _, kwargs = mock_call_llm.call_args
        self.assertEqual(kwargs["app_name"], "os.hub.game-engine")
        self.assertEqual(kwargs["models_to_try"], ["test-kernel-model"])

if __name__ == "__main__":
    unittest.main()
