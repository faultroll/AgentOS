import unittest
import builtins
import io
from contextlib import redirect_stdout
from unittest.mock import MagicMock, AsyncMock, patch
from rootfs.applets.stats import StatsApplet
from rootfs.applets.eval import EvalApplet
from rootfs.applets.sh import RunApplet

class TestApplets(unittest.IsolatedAsyncioTestCase):
    """
    AgentOS Applets 核心测试套件。
    验证各系统组件在“盲目模式”下的行为一致性。
    """

    def setUp(self):
        # 1. 模拟进程表
        self.mock_process_table = MagicMock()
        builtins._os_process_table = self.mock_process_table
        
        # 2. 模拟内核遥测
        from kernel.telemetry import global_telemetry
        global_telemetry._model_stats = {}

    async def test_stats_applet(self):
        """验证遥测展示功能"""
        applet = StatsApplet()
        f = io.StringIO()
        with redirect_stdout(f):
            await applet.run([])
        self.assertIn("Telemetry Stats", f.getvalue())

    async def test_eval_applet_flow(self):
        """集成验证：eval applet 应当通过内核实例化应用"""
        # 设置模拟应用进程
        mock_proc = MagicMock()
        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"app_state": {"final_response": "Perfect"}}
        mock_proc.instantiate.return_value = lambda: mock_agent
        
        self.mock_process_table.get.return_value = mock_proc
        
        applet = EvalApplet()
        f = io.StringIO()
        with redirect_stdout(f):
            await applet.run([])
        
        output = f.getvalue()
        self.assertIn("Running system evaluation", output)
        self.assertIn("Perfect", output)
        # 断言：必须通过内核实例化，严禁自行 import
        mock_proc.instantiate.assert_called_once()

    @patch("rootfs.applets.sh.connect_mcp")
    async def test_run_applet_forwarding(self, mock_connect_mcp):
        """集成验证：run (sh) 应当正确转发用户输入给内核实例化的应用"""
        # 设置模拟应用环境
        mock_proc = MagicMock()
        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {"app_state": {"final_response": "App Content"}}
        mock_proc.instantiate.return_value = lambda: mock_agent
        self.mock_process_table.get.return_value = mock_proc

        # 模拟 MCP 会话
        mock_session = AsyncMock()
        mock_connect_mcp.return_value.__aenter__.return_value = mock_session

        # 模拟用户输入一次后退出
        with patch("asyncio.to_thread", side_effect=["Hello", "exit"]):
            applet = RunApplet()
            f = io.StringIO()
            with redirect_stdout(f):
                await applet.run(["test-app"])
        
        output = f.getvalue()
        self.assertIn("Foreground App Execution: test-app", output)
        self.assertIn("App Content", output)
        # 核心校验：run applet 只是一个中转站，它不应该理解应用的内部原理
        mock_proc.instantiate.assert_called_once()

if __name__ == "__main__":
    unittest.main()
