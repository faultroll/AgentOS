import unittest
from kernel.compute.scheduler import ComputeScheduler
from kernel.telemetry import TelemetryBus

class TestComputeScheduler(unittest.TestCase):
    def test_scheduler_routing(self):
        """测试调度器能否根据模型配置路由"""
        bus = TelemetryBus()
        scheduler = ComputeScheduler(telemetry=bus)
        
        # 注册虚拟模型
        router_config = {"alias-1": "provider_a", "alias-2": "provider_b"}
        router_models = ["alias-1", "alias-2"]
        scheduler.register_from_config(router_config, router_models)
        
        # 对于普通的请求，应该按顺序返回
        models = scheduler.select_model(force_model=None, cost_limit="paid")
        self.assertEqual(models, ["alias-1", "alias-2"])

if __name__ == "__main__":
    unittest.main()
