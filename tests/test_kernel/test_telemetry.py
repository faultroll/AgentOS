import unittest
import logging
from kernel.telemetry import TelemetryBus

# 统一日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestTelemetry")

class TestTelemetryBus(unittest.TestCase):
    """
    内核遥测总线 (Telemetry Bus) 专项测试
    验证：事件发送、日志堆栈查询、模型健康度统计。
    """

    def test_event_emission_and_query(self):
        """
        场景：内核执行了一个 LLM 调用，需要向总线广播其结果（成功/耗时/计费）。
        预期：总线缓存中应能查到该调用记录。
        """
        logger.info("\n--- 🧪 场景：遥测事件流转 ---")
        
        # [1] Arrange
        bus = TelemetryBus(max_events=10)
        
        # [2] Act
        logger.info("📡 广播一条成功的 LLM 调用事件...")
        bus.emit_llm_call(
            app_name="validator",
            model_alias="qwen2.5",
            provider="ollama",
            latency_ms=150.0,
            token_input=100,
            token_output=50,
            success=True,
            cost=0.0
        )
        
        # [3] Assert
        logs = bus.query()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].app_name, "validator")
        self.assertEqual(logs[0].latency_ms, 150.0)
        logger.info(f"✅ 验证通过：总线已接收到来自 {logs[0].app_name} 的性能数据。")

    def test_model_health_statistics(self):
        """
        场景：调度器在选核心前，会查询核心的健康状态。
        预期：总线应能自动计算特定核心的成功率和平均延迟。
        """
        logger.info("\n--- 🧪 场景：核心健康度 (Stats) 计算 ---")

        # [1] Arrange: 模拟两次调用，一次成功一次失败
        bus = TelemetryBus()
        target_model = "shaky-model"
        bus.emit_llm_call("test-app", target_model, "p", 100.0, 0, 0, True, 0)
        bus.emit_llm_call("test-app", target_model, "p", 0.0, 0, 0, False, 0)

        # [2] Act
        stats = bus.get_model_stats(target_model)

        # [3] Assert
        self.assertEqual(stats.success_rate, 0.5)
        self.assertEqual(stats.avg_latency_ms, 100.0) # 0.0 latency for failure is ignored or averaged
        
        logger.info(f"✅ 验证通过：模型 {target_model} 健康度计算正确 (SR=50%)。")

if __name__ == "__main__":
    unittest.main()
