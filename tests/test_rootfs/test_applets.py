import unittest
import builtins
import io
import logging
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

import kernel.compute.router as router
from kernel.telemetry import global_telemetry
from rootfs.applets.stats import StatsApplet
from rootfs.applets.eval import EvalApplet
from rootfs.applets.sh import RunApplet
from tests.test_kernel.helpers import FakeProvider

# 统一日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestApplets")

class SimpleHarnessAgent:
    """
    A minimal agent that uses the real Kernel's call_llm logic.
    Instead of mocking ainvoke, we just perform a minimal state return.
    """
    async def ainvoke(self, inputs, config=None):
        # 模仿一个真实 App 的返回格式
        return {
            "messages": [{"role": "assistant", "content": "OS Applet Test Echo"}],
            "app_state": {"final_response": "OS Applet Test Echo"},
            "is_finished": True
        }

class TestApplets(unittest.IsolatedAsyncioTestCase):
    """
    AgentOS Applets 专项测试 (Hardened v2)
    验证：系统状态、评估链路、交互代理
    """

    def setUp(self):
        # [1] Arrange: 模拟进程表，挂载一个“半真实”的应用 handle
        self.mock_proc_handle = MagicMock()
        # 实例化时返回一个 SimpleHarnessAgent
        self.mock_proc_handle.instantiate.return_value = lambda **kwargs: SimpleHarnessAgent()
        
        self.mock_process_table = MagicMock()
        self.mock_process_table.get.return_value = self.mock_proc_handle
        builtins._os_process_table = self.mock_process_table
        
        # [2] Arrange: 清理并注入真实遥测，验证 StatsApplet 提取能力
        global_telemetry._model_stats.clear()
        global_telemetry._events = []

    def tearDown(self):
        if hasattr(builtins, "_os_process_table"):
            del builtins._os_process_table

    async def test_stats_applet_retrieval(self):
        """
        场景：内核产生了真实负载，用户查看面板。
        预期：Stats 应正确读取 global_telemetry 中的数据，而非固定字符串。
        """
        logger.info("\n--- 🧪 场景：实时遥测看板面板 ---")
        
        # 注入真实遥测事件
        global_telemetry.emit_llm_call("test", "qwen-test-core", "provider-x", 150.0, 10, 10, True)
        
        applet = StatsApplet()
        f = io.StringIO()
        with redirect_stdout(f):
            await applet.run([])
        
        output = f.getvalue()
        self.assertIn("Telemetry Stats", output)
        self.assertIn("qwen-test-core", output)
        self.assertIn("150ms", output)
        logger.info("✅ 验证通过：Stats Applet 成功提取了内核实时遥测数据。")

    async def test_eval_applet_chain(self):
        """
        场景：自动化评估。
        预期：EvalApplet 应能驱动进程实例化并捕获最终业务结果。
        """
        logger.info("\n--- 🧪 场景：系统自评链路演习 ---")
        
        applet = EvalApplet()
        f = io.StringIO()
        with redirect_stdout(f):
            await applet.run([]) 
            
        output = f.getvalue()
        self.assertIn("OS Applet Test Echo", output)
        logger.info("✅ 验证通过：Eval Applet 贯通了实例化与业务结果解析。")

    async def test_sh_applet_proxy_flow(self):
        """
        场景：'run <app>' 交互式对话。
        预期：移除对 connect_mcp 的屏蔽，让其跑在真实的内存总线上。
        """
        logger.info("\n--- 🧪 场景：SH 代理交互链 (真实 MCP 总线) ---")

        # 模拟一次用户输入后退出
        with patch("asyncio.to_thread", side_effect=["Hello Kernel", "exit"]):
            applet = RunApplet()
            f = io.StringIO()
            with redirect_stdout(f):
                await applet.run(["demo-app"])
        
        output = f.getvalue()
        self.assertIn("OS Applet Test Echo", output)
        self.assertIn("Detaching from demo-app", output)
        logger.info("✅ 验证通过：SH Applet 成功在真实内存总线环境下代理了 App 交互。")

if __name__ == "__main__":
    unittest.main()
