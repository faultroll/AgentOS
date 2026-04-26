import unittest
import logging
import time
from kernel.compute.scheduler import ComputeScheduler, ModelProfile
from kernel.telemetry import TelemetryBus

# 统一日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestScheduler")

class TestComputeScheduler(unittest.TestCase):
    """
    内核调度器专项测试 (Hardened)
    验证：规格感知、健康反馈 (Feedback Loop)、成本策略
    """

    def setUp(self):
        self.bus = TelemetryBus()
        self.scheduler = ComputeScheduler(telemetry=self.bus)

    def test_dynamic_reordering_on_failure(self):
        """
        场景：两个同规格模型，其中一个开始报错。
        预期：故障模型的成功率下降，调度器应自动将其排序后移（Feedback Loop）。
        """
        logger.info("\n--- 🧪 场景：健康反馈闭环 (Feedback Loop) ---")
        
        # [1] Arrange
        self.scheduler.register_model(ModelProfile("model-good", "p1", priority=10))
        self.scheduler.register_model(ModelProfile("model-shaky", "p1", priority=10))
        
        # 初始状态：两者优先级相同，排序可能按字母或注册顺序
        initial = self.scheduler.select_model()
        logger.info(f"初始序列: {initial}")

        # [2] Act: 模拟 model-shaky 连续失败
        for _ in range(3):
            self.bus.emit_llm_call("app", "model-shaky", "p", 0.0, 0, 0, success=False)
        
        # [3] Assert: model-shaky 因进入 Cooldown 应被排除在列表之外
        logger.info("📡 模拟故障后重新调度...")
        reordered = self.scheduler.select_model()
        logger.info(f"重排后序列: {reordered}")
        
        self.assertIn("model-good", reordered)
        self.assertNotIn("model-shaky", reordered, "处于 Cooldown 期的模型应被物理隔离")
        
        logger.info("✅ 验证通过：调度器正确执行了故障隔离策略。")

    def test_context_window_sensing_penalty(self):
        """
        场景：任务 Token 超过小核心上限。
        预期：小核心被巨量降权（Penalize），大核心上位。
        """
        logger.info("\n--- 🧪 场景：规格感知惩罚 (Context Sensing) ---")

        # [1] Arrange
        self.scheduler.register_model(ModelProfile("small-core", "p", context_window=4000, priority=10))
        self.scheduler.register_model(ModelProfile("big-core", "p", context_window=128000, priority=50))
        
        # [2] Act: 发送一个 10k 的任务
        models = self.scheduler.select_model(estimated_tokens=10000)
        
        # [3] Assert
        self.assertEqual(models[0], "big-core", "大任务应自动选择大核心，即便大核心原始优先级较低")
        logger.info("✅ 验证通过：规格感知降权逻辑生效。")

if __name__ == "__main__":
    unittest.main()
