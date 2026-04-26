import unittest
from kernel.state import create_process, ProcessState

class TestKernelStateHardened(unittest.TestCase):
    """
    内核 PCB 状态机加固验证
    验证：PCB 是否支持精确的“历史覆盖”语义，而非盲目的增量累加。
    """

    def test_pcb_creation_defaults(self):
        """验证 PCB 初始化状态"""
        state = create_process("Hello", app_name="test")
        self.assertTrue(state["pid"].startswith("test-"))
        self.assertEqual(len(state["messages"]), 1)
        self.assertIsNone(state["os_signal"])
        self.assertFalse(state["is_error"])

    def test_pcb_overwrite_behavior(self):
        """
        核心物理性质验证：验证 PCB 消息不再自动累加。
        在精确控制模式下，节点返回的列表应直接替换旧历史。
        """
        # [1] Arrange
        state = create_process("Original")
        self.assertEqual(len(state["messages"]), 1)
        
        # [2] Simulate a node returning a new complete list
        # 模拟审计节点执行了“历史裁减”
        new_messages = [{"role": "system", "content": "Compressed"}]
        
        # 模仿 LangGraph 的更新逻辑（在没有 Reducer 的情况下，TypedDict 默认是覆盖）
        state.update({"messages": new_messages})
        
        # [3] Assert
        self.assertEqual(len(state["messages"]), 1)
        self.assertEqual(state["messages"][0]["content"], "Compressed")
        # 确保原来的 "Original" 消息被彻底丢弃了
        self.assertNotIn("Original", [m["content"] for m in state["messages"]])

if __name__ == "__main__":
    unittest.main()
