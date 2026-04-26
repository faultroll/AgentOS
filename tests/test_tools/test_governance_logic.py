import unittest
import json
import os
import shutil
import builtins
import logging
from unittest.mock import patch
from kernel.state import create_process
from tools.memory import register
from mcp.server.fastmcp import FastMCP
import kernel.compute.router as router
from kernel.compute.scheduler import ComputeScheduler, ModelProfile
from kernel.telemetry import global_telemetry
from tests.test_kernel.helpers import FakeProvider

class TestGovernanceLogic(unittest.IsolatedAsyncioTestCase):
    """
    [ROOTFS TEST] 治理引擎物理契约测试。
    验证 govern_context 工具在不依赖 App 拓扑的情况下的逻辑确定性。
    """
    
    async def asyncSetUp(self):
        # 1. 物理环境
        self.test_dir = "tmp/test_gov_vault"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        
        # 2. 注入真实驱动 (FakeProvider) 替代 AsyncMock
        self.old_instances = router.PROVIDER_INSTANCES.copy()
        router.PROVIDER_INSTANCES.clear()
        self.p_fake = FakeProvider("p_fake_gov", response_data={
            "choices": [{"message": {"role": "assistant", "content": "# 治理摘要\n核心内容已压缩。"}}]
        })
        router.PROVIDER_INSTANCES["p_fake"] = self.p_fake
        self.config_patcher = patch("config.ROUTER_CONFIG", {"cheap-core": "p_fake"})
        self.config_patcher.start()

        # 3. 调度器注入
        self.test_bus = global_telemetry
        self.scheduler = ComputeScheduler(telemetry=self.test_bus)
        self.scheduler.register_model(ModelProfile(alias="cheap-core", provider="p_fake", cost_tier="free", priority=10))
        builtins._os_scheduler = self.scheduler

        # 4. 注册工具
        self.mcp = FastMCP("test_gov")
        register(self.mcp, base_dir=self.test_dir)

    async def asyncTearDown(self):
        router.PROVIDER_INSTANCES.clear()
        router.PROVIDER_INSTANCES.update(self.old_instances)
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if hasattr(builtins, "_os_scheduler"):
            del builtins._os_scheduler

    async def test_semantic_salvage_logic(self):
        """验证语义打捞逻辑：强制保留 User 消息。"""
        messages = [
            {"role": "system", "content": "OS"},
            {"role": "user", "content": "Critical intent: Antigravity"},
            {"role": "assistant", "content": "Thinking..."},
            {"role": "assistant", "content": "Final resp."}
        ]
        
        # 获取工具函数
        govern_tool_func = self.mcp._tool_manager.get_tool("govern_context").fn
        
        result_json = await govern_tool_func(
            messages_json=json.dumps(messages),
            os_signal="CONTEXT_PRESSURE"
        )
        governed = json.loads(result_json)
        
        # System + Summary + User(打捞) + last 2 = 5
        self.assertEqual(len(governed), 5)
        self.assertEqual(governed[2]["role"], "user")
        self.assertIn("Antigravity", governed[2]["content"])
        print("✅ 纯物理驱动下的语义打捞验证通过。")

    async def test_threshold_logic(self):
        """验证治理门槛：短对话不执行压缩。"""
        messages = [{"role": "system", "content": "A"}, {"role": "user", "content": "B"}]
        govern_tool_func = self.mcp._tool_manager.get_tool("govern_context").fn
        
        result_json = await govern_tool_func(
            messages_json=json.dumps(messages),
            os_signal="CONTEXT_PRESSURE"
        )
        governed = json.loads(result_json)
        
        self.assertEqual(len(governed), 2)
        print("✅ 纯物理驱动下的治理阈值验证通过。")

if __name__ == "__main__":
    unittest.main()
