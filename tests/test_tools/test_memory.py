import unittest
import os
import shutil
import json
import logging
import builtins
from unittest.mock import patch

import config
import kernel.compute.router as router
from kernel.compute.scheduler import ComputeScheduler, ModelProfile
from kernel.telemetry import global_telemetry
from kernel.state import create_process
from mcp.server.fastmcp import FastMCP
from tools.memory import register
from tests.test_kernel.helpers import FakeProvider

# 统一日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestMemoryTool")

TEST_MEM_DIR = "tmp/test_mem_standalone"

class TestMemoryToolHardened(unittest.IsolatedAsyncioTestCase):
    """
    [ROOTFS TEST] 记忆工具物理回归测试。
    验证：在不依赖任何应用框架的情况下，工具链能够真实驱动内核路由器完成治理并物理落盘。
    """

    async def asyncSetUp(self):
        # [1] 物理隔离环境
        if os.path.exists(TEST_MEM_DIR):
            shutil.rmtree(TEST_MEM_DIR)
        os.makedirs(TEST_MEM_DIR)
        self.old_mem_dir = config.MEMORY_DIR
        config.MEMORY_DIR = TEST_MEM_DIR
        
        # [2] 注入 FakeProvider：模拟物理驱动返回
        self.old_instances = router.PROVIDER_INSTANCES.copy()
        router.PROVIDER_INSTANCES.clear()
        
        self.p_fake = FakeProvider("p_fake", response_data={
            "choices": [{"message": {"role": "assistant", "content": "# 压缩摘要\n- 验证了物理隔离。"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        })
        router.PROVIDER_INSTANCES["p_fake"] = self.p_fake
        
        # 劫持物理映射
        self.config_patcher = patch("config.ROUTER_CONFIG", {"cheap-core": "p_fake"})
        self.config_patcher.start()

        # [3] 注入调度器 (OS 全局单例模拟)
        self.test_bus = global_telemetry
        self.scheduler = ComputeScheduler(telemetry=self.test_bus)
        self.scheduler.register_model(ModelProfile(alias="cheap-core", provider="p_fake", cost_tier="free", priority=10))
        builtins._os_scheduler = self.scheduler
        
        # [4] 启动工具服务
        self.mcp = FastMCP("test_memory")
        register(self.mcp, base_dir=TEST_MEM_DIR)

    async def asyncTearDown(self):
        router.PROVIDER_INSTANCES.clear()
        router.PROVIDER_INSTANCES.update(self.old_instances)
        config.MEMORY_DIR = self.old_mem_dir
        self.config_patcher.stop()
        if os.path.exists(TEST_MEM_DIR):
            shutil.rmtree(TEST_MEM_DIR)
        if hasattr(builtins, "_os_scheduler"):
            del builtins._os_scheduler

    async def test_govern_context_physical_flow(self):
        """场景：OS 通过 govern_context 工具强制执行上下文治理。"""
        # [1] Prepare
        messages = [
            {"role": "system", "content": "You are AgentOS."},
            {"role": "user", "content": "Keep me!"},
            {"role": "assistant", "content": "Ok."},
            {"role": "assistant", "content": "Tail message."}
        ]
        
        # [2] Act: 模拟物理调用
        govern_tool = self.mcp._tool_manager.get_tool("govern_context")
        result_json = await govern_tool.fn(
            messages_json=json.dumps(messages),
            os_signal="CONTEXT_PRESSURE"
        )
        governed = json.loads(result_json)
        
        # [3] Assert
        # 验证物理长度 (System + Summary + User + last 2)
        # 根据我们 1+1+1+2 逻辑，应该是 5
        self.assertEqual(len(governed), 5)
        
        # 验证物理文件落盘
        summary_dir = os.path.join(TEST_MEM_DIR, "summaries")
        self.assertTrue(os.path.exists(summary_dir))
        self.assertTrue(len(os.listdir(summary_dir)) > 0, "摘要文件未真实写入磁盘。")
        print("✅ 治理工具物理流转验证通过。")

if __name__ == "__main__":
    unittest.main()
