import unittest
import os
import shutil
import logging
import builtins
from unittest.mock import patch

import config
import kernel.compute.router as router
from kernel.compute.scheduler import ComputeScheduler, ModelProfile
from kernel.telemetry import global_telemetry
from kernel.state import create_process
from apps.intent_proxy.app import intent_proxy_app
from tests.test_kernel.helpers import FakeProvider

# 统一日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestIntentProxyIntegration")

TEST_MEM_DIR = "test_intent_vault"

class TestIntentProxyFullChain(unittest.IsolatedAsyncioTestCase):
    """
    Intent Proxy 全链路集成测试 (Robust v2)
    验证：Architecture -> Persist (Memory Write) -> Worker -> Telemetry
    策略：直接劫持 config.py 中定义的真实模型别名，强制重定向物理流量。
    """

    async def asyncSetUp(self):
        # [1] 强制路径隔离
        if os.path.exists(TEST_MEM_DIR):
            shutil.rmtree(TEST_MEM_DIR)
        os.makedirs(TEST_MEM_DIR)
        
        self.old_mem_dir = config.MEMORY_DIR
        config.MEMORY_DIR = TEST_MEM_DIR
        # 显式注入环境变量，确保某些依赖环境变量的底层工具也能感知
        os.environ["MEMORY_DIR"] = TEST_MEM_DIR
        
        # [2] 劫持物理 Provider 实例
        # 策略：不改配置映射，直接改 Provider 实例池，确保 architect-local 等核心直接指向 FakeProvider
        self.old_instances = router.PROVIDER_INSTANCES.copy()
        router.PROVIDER_INSTANCES.clear()
        
        # 构造架构师的返回负载
        fake_response = {
            "choices": [{"message": {
                "role": "assistant", 
                "content": "<thought>I must remember this. [PERSIST]: Identity | User is Antigravity.</thought><blueprint>Greet the user</blueprint>"
            }}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10}
        }
        self.p_fake = FakeProvider("p_fake", response_data=fake_response)
        
        # 劫持 config 中可能出现的所有核心名
        for model_alias in config.ROUTER_MODELS:
            provider_name = config.ROUTER_CONFIG.get(model_alias)
            if provider_name:
                router.PROVIDER_INSTANCES[provider_name] = self.p_fake

        # [3] 重置遥测总线与调度器
        self.test_bus = global_telemetry
        self.test_bus._events.clear()
        self.test_bus._model_stats.clear()
        
        # 沿用真实的调度器实例
        self.scheduler = ComputeScheduler(telemetry=self.test_bus)
        # 确保调度器里能找到这些核心
        for model in config.ROUTER_MODELS:
            self.scheduler.register_model(ModelProfile(
                alias=model,
                provider=config.ROUTER_CONFIG.get(model, "unknown"),
                context_window=config.MODEL_METADATA.get(model, {}).get("context_window", 8000)
            ))
        builtins._os_scheduler = self.scheduler

    async def asyncTearDown(self):
        router.PROVIDER_INSTANCES.clear()
        router.PROVIDER_INSTANCES.update(self.old_instances)
        config.MEMORY_DIR = self.old_mem_dir
        if os.path.exists(TEST_MEM_DIR):
            shutil.rmtree(TEST_MEM_DIR)
        if hasattr(builtins, "_os_scheduler"):
            del builtins._os_scheduler

    async def test_full_pipeline_with_physical_persistence(self):
        """
        场景：Intent Proxy 全链路执行。
        由于我们劫持了 Provider 实例池，即便 Node 内部硬编码了核心名，
        流量也会穿过真实的 CallLLM 抵达我们的 FakeProvider。
        """
        logger.info("\n--- 🧪 场景：Intent Proxy 全链路“架构师思考”真核演习 ---")

        # [Action] 发起进程
        initial_state = create_process("Who am I?", app_name="intent-proxy")
        
        # 运行应用
        final_state = await intent_proxy_app.ainvoke(initial_state)
        
        # [Assert 1] 业务结果
        self.assertIn("plan_intelligence", final_state["app_state"])
        
        # [Assert 2] 物理持久化 (注意：MCP 工具会自动把标题转为小写)
        fact_file = os.path.join(TEST_MEM_DIR, "facts", "identity.md")
        self.assertTrue(os.path.exists(fact_file), f"持久化失效：{fact_file} 未生成。")
        
        with open(fact_file, "r") as f:
            self.assertIn("User is Antigravity", f.read())
        logger.info(f"✅ 物理验证通过：全链路运行并成功落盘事实。")

if __name__ == "__main__":
    unittest.main()
