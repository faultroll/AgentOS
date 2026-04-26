import unittest
import logging
import kernel.compute.router as router
from kernel.compute.router import call_llm
from kernel.telemetry import TelemetryBus
from tests.test_kernel.helpers import FakeProvider

# 统一日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestRouter")

class TestComputeRouter(unittest.IsolatedAsyncioTestCase):
    """
    内核路由器专项测试 (Hardened)
    验证：Best-effort 交付、Fallback 机制、遥测反馈、信号注入
    """

    def setUp(self):
        # 备份并替换全局 Provider 实例，避免真实网络调用
        self.old_instances = router.PROVIDER_INSTANCES.copy()
        router.PROVIDER_INSTANCES.clear()
        
        # 准备一个新鲜的遥测总线
        self.test_bus = TelemetryBus()

    def tearDown(self):
        # 还原 Provider 实例
        router.PROVIDER_INSTANCES.clear()
        router.PROVIDER_INSTANCES.update(self.old_instances)

    async def test_should_inject_pressure_signal_under_load(self):
        """
        场景：大负载请求（约 85% 容量）。
        预期：成功返回结果，并注入 CONTEXT_PRESSURE 信号。
        """
        logger.info("\n--- 🧪 场景：软溢出压测 (Context Pressure) ---")
        
        # [1] Arrange
        router.PROVIDER_INSTANCES["fake_p"] = FakeProvider("fake_p")
        test_config = {"qwen-8k": "fake_p"}
        
        # 构造约 6.8k tokens 的 Payload
        heavy_payload = [{"role": "user", "content": "X" * 24000}] 

        # [2] Act
        data = await call_llm(
            messages=heavy_payload,
            models_to_try=["qwen-8k"],
            router_config=test_config,
            telemetry=self.test_bus
        )

        # [3] Assert
        self.assertEqual(data.get("os_signal"), "CONTEXT_PRESSURE")
        self.assertEqual(len(self.test_bus.query()), 1, "遥测总线应记录一次调用")
        logger.info("✅ 验证通过：信号注入成功，遥测记录正常。")

    async def test_fallback_sequence_on_provider_error(self):
        """
        场景：序列中的第一个模型提供商故障（500 错误）。
        预期：内核应自动尝试序列中的第二个模型。
        """
        logger.info("\n--- 🧪 场景：内核 Fallback 容灾演习 ---")

        # [1] Arrange
        p1 = FakeProvider("fail_p", behavior="500")
        p2 = FakeProvider("success_p", behavior="success")
        router.PROVIDER_INSTANCES["fail_p"] = p1
        router.PROVIDER_INSTANCES["success_p"] = p2
        
        test_config = {
            "model-a": "fail_p",
            "model-b": "success_p"
        }

        # [2] Act
        logger.info("📡 发起请求，首选 model-a (预期故障)...")
        data = await call_llm(
            messages=[{"role": "user", "content": "hi"}],
            models_to_try=["model-a", "model-b"],
            router_config=test_config,
            telemetry=self.test_bus
        )

        # [3] Assert
        self.assertEqual(p1.call_count, 1)
        self.assertEqual(p2.call_count, 1)
        self.assertIn("Fake response", data["choices"][0]["message"]["content"])
        
        # 验证遥测中有两条记录，一败一成
        logs = self.test_bus.query()
        self.assertEqual(len(logs), 2)
        self.assertFalse(logs[0].success)
        self.assertTrue(logs[1].success)
        
        logger.info("✅ 验证通过：Fallback 机制完美触发，业务无感切换。")

    async def test_all_providers_failure_handling(self):
        """
        场景：所有备选模型均不可用。
        预期：内核应优雅报错，不崩溃，并记录所有失败。
        """
        logger.info("\n--- 🧪 场景：全链路崩溃防御 ---")

        # [1] Arrange
        router.PROVIDER_INSTANCES["bad_p"] = FakeProvider("bad_p", behavior="429")
        test_config = {"m1": "bad_p", "m2": "bad_p"}

        # [2] Act
        data = await call_llm(
            messages=[{"role": "user", "content": "hi"}],
            models_to_try=["m1", "m2"],
            router_config=test_config,
            telemetry=self.test_bus
        )

        # [3] Assert
        self.assertIn("Error", data["choices"][0]["message"]["content"])
        self.assertEqual(len(self.test_bus.query()), 2)
        logger.info("✅ 验证通过：全链路失效时正确返回错误信息并记录遥测。")

if __name__ == "__main__":
    unittest.main()
