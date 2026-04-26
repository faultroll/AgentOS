import unittest
import os
import shutil
import config
from apps.intent_proxy.nodes import architect_node, context_audit_node, memory_recall_node, memory_reflect_node
from kernel.state import create_process

TEST_MEM_DIR = "test_node_vault"

class TestIntentProxyNodesHardened(unittest.IsolatedAsyncioTestCase):
    """
    Intent Proxy 节点单元测试 (Robust v2)
    验证：物理 I/O 贯通，以及信号驱动的审计逻辑。
    """

    async def asyncSetUp(self):
        # [1] 强制物理路径重置
        if os.path.exists(TEST_MEM_DIR):
            shutil.rmtree(TEST_MEM_DIR)
        os.makedirs(TEST_MEM_DIR)
        
        self.old_mem_dir = config.MEMORY_DIR
        config.MEMORY_DIR = TEST_MEM_DIR
        # 同步环境变量
        os.environ["MEMORY_DIR"] = TEST_MEM_DIR

    async def asyncTearDown(self):
        config.MEMORY_DIR = self.old_mem_dir
        if os.path.exists(TEST_MEM_DIR):
            shutil.rmtree(TEST_MEM_DIR)

    async def test_memory_recall_node_physical(self):
        """测试记忆检索：真实读取磁盘文件"""
        # [Arrange] 物理生成事实文件 (注意：MCP 驱动保存时会将文件名转为小写)
        fact_path = os.path.join(TEST_MEM_DIR, "facts")
        os.makedirs(fact_path)
        with open(os.path.join(fact_path, "context.md"), "w", encoding="utf-8") as f:
            f.write("# Identity\nUser is checking physical memory recall.")

        # [Act]
        state = create_process("Who is checking?")
        result = await memory_recall_node(state)
        
        # [Assert] 验证 app_state 中的内容
        recalled = result["app_state"]["relevant_memory"][0]["content"]
        self.assertIn("physical memory recall", recalled)

    async def test_memory_reflect_node_physical(self):
        """测试记忆反思：真实写入磁盘文件"""
        # [Arrange]
        state = create_process("test")
        state["app_state"] = {
            "plan_intelligence": {
                "thought": "Remember this: [PERSIST]: User_Status | High_Alert."
            }
        }

        # [Act]
        await memory_reflect_node(state)
        
        # [Assert] 模型反射应生成文件
        # 注意：MCP 工具保存 save_fact 会将 'User_Status' 转为 'user_status.md'
        fact_file = os.path.join(TEST_MEM_DIR, "facts", "user_status.md")
        self.assertTrue(os.path.exists(fact_file), f"持久化失败：{fact_file} 未生成。")
        with open(fact_file, "r") as f:
            self.assertIn("High_Alert", f.read())

    async def test_context_audit_node_signal_trigger(self):
        """
        测试上下文审计：验证信号触发的认知压缩。
        逻辑：只有当 os_signal 为 CONTEXT_PRESSURE 时，才会返回新的 messages。
        """
        # [1] Arrange: 构造压力场景 (5 条消息)
        state = create_process("query")
        state["os_signal"] = "CONTEXT_PRESSURE"
        state["messages"] = [
            {"role": "system", "content": "OS Console"}, # m[0]
            {"role": "user", "content": "History A"},
            {"role": "assistant", "content": "History B"},
            {"role": "user", "content": "Recent C"},   # tail[0]
            {"role": "assistant", "content": "Recent D"} # tail[1]
        ]
        
        # [2] Act: 调用审计节点
        result = await context_audit_node(state)
        
        # [3] Assert
        self.assertIn("messages", result, "审计节点在压力下应返回压缩后的消息序列")
        # 压缩后的结构应为：System + Summary + 最近 2 条 (共 4 条)
        self.assertEqual(len(result["messages"]), 4)
        self.assertIn("摘要", result["messages"][1]["content"])

if __name__ == "__main__":
    unittest.main()
