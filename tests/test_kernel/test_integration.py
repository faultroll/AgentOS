import unittest
import logging
import config
import kernel.compute.router as router
from kernel.compute.router import call_llm
from kernel.telemetry import TelemetryBus
from tests.test_kernel.helpers import FakeProvider

# 统一日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestKernelIntegration")

class TestKernelIntegration(unittest.IsolatedAsyncioTestCase):
    """
    内核全链路集成测试 (Robust Version)
    验证：State -> Scheduler -> Router -> Telemetry 的完整闭环
    策略：劫持 config 中的真实模型别名，绕过常量 Mock 失败问题
    """

    def setUp(self):
        # 备份并清理全局 Provider 实例
        self.old_instances = router.PROVIDER_INSTANCES.copy()
        router.PROVIDER_INSTANCES.clear()
        
        # 准备测试总线
        self.test_bus = TelemetryBus()
        
        # 创建两个 Fake Provider
        self.p_small = FakeProvider("p_small")
        self.p_big = FakeProvider("p_big")
        router.PROVIDER_INSTANCES["p_small"] = self.p_small
        router.PROVIDER_INSTANCES["p_big"] = self.p_big

        # 映射真实 config 中存在的模型名称
        # architect-local 规格是 32k
        # qwen/qwen3-coder:free 规格是 8k
        self.mapped_config = {
            "architect-local": "p_big",
            "qwen/qwen3-coder:free": "p_small"
        }

    def tearDown(self):
        router.PROVIDER_INSTANCES.clear()
        router.PROVIDER_INSTANCES.update(self.old_instances)

    async def test_full_chain_auto_selection_and_telemetry(self):
        """
        场景：发起一个超过 8k 的大任务，观察内核是否自动调度到 32k 核心。
        预期：
          1. 调度器识别出 10k 任务超出了 qwen (8k) 的承受范围。
          2. 自动选择执行路线：architect-local (p_big)。
          3. 遥测总线记录该行为。
        """
        logger.info("\n--- 🧪 场景：内核全链路劫持集成演习 ---")

        # [1] Arrange: 构造约 10k tokens 的任务
        messages = [{"role": "user", "content": "X" * 35000}] 

        # [2] Act: 调用内核
        # 我们显式传入 router_config，内核会优先使用它进行 Provider 查找
        data = await call_llm(
            messages=messages,
            models_to_try=None, # 强制触发调度器
            router_config=self.mapped_config,
            telemetry=self.test_bus,
            app_name="integration-test"
        )

        # [3] Assert
        # 验证 p_big 被调用（代表调度到了 architect-local）
        self.assertEqual(self.p_big.call_count, 1, "大任务应调度至大核心 (p_big/architect-local)")
        self.assertEqual(self.p_small.call_count, 0, "大任务不应调用小核心")
        
        # 验证遥测
        logs = self.test_bus.query()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].model_alias, "architect-local")
        self.assertEqual(logs[0].success, True)
        
        logger.info(f"✅ 验证通过：全链路闭环正常，自动调度至：{logs[0].model_alias}")

if __name__ == "__main__":
    unittest.main()
