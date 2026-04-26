import unittest
import asyncio
from kernel.telemetry import TelemetryBus

class TestTelemetryBus(unittest.TestCase):
    def test_emit_llm_call(self):
        """测试遥测总线事件发送逻辑"""
        bus = TelemetryBus(max_events=10)
        bus.emit_llm_call("test_app", "test_model", "test_provider", 120.0, 10, 20, True, 0.0)
        
        logs = bus.query()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].app_name, "test_app")
        self.assertEqual(logs[0].model_alias, "test_model")

if __name__ == "__main__":
    unittest.main()
