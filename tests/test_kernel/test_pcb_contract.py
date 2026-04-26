import unittest
from kernel.state import create_process

class TestKernelPCBContract(unittest.TestCase):
    """
    AgentOS 内核 PCB 契约校验
    遵循‘盲目性原则’：不依赖应用层框架，只验证 OS 级状态载体。
    """

    def test_pcb_state_isolation(self):
        """验证 PCB 的物理隔离性"""
        p1 = create_process("Query 1")
        p2 = create_process("Query 2")
        
        self.assertNotEqual(p1["pid"], p2["pid"])
        
        # 修改 p1，不应影响 p2
        p1["os_signal"] = "PRESSURE"
        self.assertIsNone(p2["os_signal"])

    def test_pcb_content_integrity(self):
        """验证 PCB 是否支持内核信号的精准注入"""
        state = create_process("Initial")
        
        # 模拟内核发现上下文压力并进行信号注入
        state["os_signal"] = "CONTEXT_PRESSURE"
        state["messages"].append({"role": "assistant", "content": "Overflowing..."})
        
        # 验证物理字段完备性
        self.assertEqual(state["os_signal"], "CONTEXT_PRESSURE")
        self.assertEqual(len(state["messages"]), 2)
        self.assertIn("pid", state)

    def test_pcb_opaque_app_state(self):
        """验证 app_state 的不透明容器属性"""
        state = create_process("Test")
        
        # 内核只负责搬运 app_state 元组或字典
        complex_app_data = {"langgraph_version": "0.1", "nodes_run": ["recall"]}
        state["app_state"] = complex_app_data
        
        self.assertEqual(state["app_state"]["nodes_run"][0], "recall")

if __name__ == "__main__":
    unittest.main()
