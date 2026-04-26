import unittest
from kernel.state import _merge_messages, create_process

class TestKernelState(unittest.TestCase):
    def test_merge_messages(self):
        """测试 LangGraph 的消息合并函数"""
        left = [{"role": "user", "content": "hello"}]
        right = [{"role": "assistant", "content": "hi"}]
        expected = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
        self.assertEqual(_merge_messages(left, right), expected)

    def test_create_process(self):
        """测试状态初始化"""
        state = create_process("test query", app_name="test-app")
        self.assertEqual(state["messages"][0]["content"], "test query")
        self.assertFalse(state["is_finished"])
        self.assertEqual(state["token_usage"], 0)
        self.assertTrue(state["pid"].startswith("test-app"))

if __name__ == "__main__":
    unittest.main()
