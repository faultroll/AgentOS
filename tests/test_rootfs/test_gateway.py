import unittest
import builtins
import logging
from fastapi.testclient import TestClient
from unittest.mock import patch

import config
import kernel.compute.router as router
from kernel.compute.scheduler import ComputeScheduler, ModelProfile
from kernel.telemetry import global_telemetry as test_bus
from rootfs.applets.gateway import app
from tests.test_kernel.helpers import FakeProvider

# 统一日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestGateway")

class TestGateway(unittest.IsolatedAsyncioTestCase):
    """
    AgentOS Gateway 专项测试 (Hardened v2)
    验证：OpenAI 协议兼容性、全链路转发 (Gateway -> Router -> FakeProvider)
    """
    
    def setUp(self):
        self.client = TestClient(app)
        
        # [1] Arrange: 拦截物理层（Provider 实例池）
        self.old_instances = router.PROVIDER_INSTANCES.copy()
        router.PROVIDER_INSTANCES.clear()
        
        self.p_fake = FakeProvider("p_fake", response_data={
            "choices": [{"message": {"role": "assistant", "content": "Gateway integration OK"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10}
        })
        router.PROVIDER_INSTANCES["p_fake"] = self.p_fake
        
        # [2] Arrange: 使用全局遥测总线并注入真实调度器
        self.test_bus = test_bus
        self.test_bus._events.clear()
        self.test_bus._model_stats.clear()
        
        self.scheduler = ComputeScheduler(telemetry=self.test_bus)
        
        # 注册一个测试用的核心，并确保映射指向我们的 p_fake
        self.scheduler.register_model(ModelProfile(
            alias="gateway-test-core", 
            provider="p_fake", 
            context_window=8192
        ))
        
        # 挂载到系统全局单例 (Rootfs 与 Kernel 之前的物理连接点)
        builtins._os_scheduler = self.scheduler

    def tearDown(self):
        # 还原物理环境
        router.PROVIDER_INSTANCES.clear()
        router.PROVIDER_INSTANCES.update(self.old_instances)
        if hasattr(builtins, "_os_scheduler"):
            del builtins._os_scheduler

    def test_v1_models_live_sync(self):
        """
        场景：通过网关查询可用核心。
        预期：Gateway 应返回调度器中注册的真实名称 'gateway-test-core'。
        """
        logger.info("\n--- 🧪 场景：实时核心列表同步 ---")
        response = self.client.get("/v1/models")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        model_ids = [m["id"] for m in data["data"]]
        self.assertIn("gateway-test-core", model_ids)
        logger.info(f"✅ 验证通过：Gateway 正确映射了调度器中的模型。")

    async def test_full_chain_hijack_routing(self):
        """
        验证全链路：HTTP -> Gateway -> CallLLM -> FakeProvider
        预期：不进行 call_llm 的 Mock，链路应物理闭环。
        """
        logger.info("\n--- 🧪 场景：网关全链路协议转发验证 ---")

        payload = {
            "model": "game-engine:gateway-test-core",
            "messages": [{"role": "user", "content": "Test Gateway Flow"}]
        }
        
        # 核心：必须 Mock 掉 config 中的映射，因为 call_llm 是从 config 读映射的
        mapped_config = {"gateway-test-core": "p_fake"}
        with patch("config.ROUTER_CONFIG", mapped_config), \
             patch("config.MODEL_METADATA", {"gateway-test-core": {"context_window": 8192}}):
            
            # [Act] 通过 TestClient 发起真实 HTTP 请求
            response = self.client.post("/v1/chat/completions", json=payload)
        
        # [Assert]
        self.assertEqual(response.status_code, 200)
        resp_json = response.json()
        self.assertIn("Gateway integration OK", resp_json["choices"][0]["message"]["content"])
        
        # 验证物理计数
        self.assertEqual(self.p_fake.call_count, 1, "全链路未打通：FakeProvider 未探测到调用。")
        
        # 验证遥测总线是否捕获到了网关标签
        event = self.test_bus.query()[0]
        self.assertEqual(event.app_name, "os.hub.game-engine")
        
        logger.info("✅ 验证通过：网关劫持、内核转发、遥测采集全链路物理验证成功。")

if __name__ == "__main__":
    unittest.main()
