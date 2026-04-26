import os
import shutil
import unittest
import logging
from pathlib import Path

# 关键：在导入任何内核/工具模块之前，强制设定测试目录环境变量
TEST_MEMORY_DIR = "test_memory_vault"
os.environ["MEMORY_DIR"] = TEST_MEMORY_DIR

import config
from kernel.drivers.mcp_connect import connect_mcp

# 统一日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestMemoryIO")

class TestMemoryRealIO(unittest.IsolatedAsyncioTestCase):
    """
    内存持久化集成测试 (Real IO)
    验证：数据通过 MCP 总线 -> 磁盘持久化 -> 语义召回的完整生命周期
    """
    
    async def asyncSetUp(self):
        """测试前清理并创建临时仓库，并强制覆盖全局 config 防止单例污染"""
        if os.path.exists(TEST_MEMORY_DIR):
            shutil.rmtree(TEST_MEMORY_DIR)
        os.makedirs(TEST_MEMORY_DIR)
        
        # 核心修复：强制修改已在大进程中加载的 config 模块
        self._old_memory_dir = config.MEMORY_DIR
        config.MEMORY_DIR = TEST_MEMORY_DIR

    async def asyncTearDown(self):
        """测试后销毁临时仓库，并还原配置"""
        if os.path.exists(TEST_MEMORY_DIR):
            shutil.rmtree(TEST_MEMORY_DIR)
        config.MEMORY_DIR = self._old_memory_dir

    async def test_mcp_memory_lifecycle(self):
        """
        场景：存储一个事实，验证其物理存在，并通过语义搜索召回。
        预期：文件在磁盘生成，且 recall_memory 能搜到相关内容。
        """
        logger.info("\n--- 🧪 场景：内存全链路持久化验证 ---")

        async with connect_mcp(transport="in_memory") as session:
            
            # [1] Arrange: 定义一个要存储的虚构事实
            fact_title = "Quantum_Safety_Protocol"
            fact_content = "The quantum encryption key is stored in vault-7."
            
            # [2] Act: 写入内存 (Write)
            logger.info(f"📥 正在执行 save_fact -> {TEST_MEMORY_DIR}...")
            save_result = await session.call_tool("save_fact", {
                "title": fact_title,
                "content": fact_content
            })
            
            # [3] Assert Part 1: 物理校验
            fact_file = Path(TEST_MEMORY_DIR) / "facts" / "quantum_safety_protocol.md"
            self.assertTrue(fact_file.exists(), f"❌ 物理校验失败：文件未生成于 {fact_file}")
            logger.info("📂 物理校验通过：磁盘已生成 Markdown 事实文件。")

            # [4] Act: 语义召回 (Read/Recall)
            logger.info("🔍 正在执行 recall_memory (Query: 'encryption key')...")
            recall_result = await session.call_tool("recall_memory", {
                "query": "encryption key"
            })
            
            # [5] Assert Part 2: 内容校验
            recall_text = recall_result.content[0].text
            self.assertIn("vault-7", recall_text)
            self.assertIn("Source: quantum_safety_protocol.md", recall_text)
            
            logger.info("✅ 验证通过：召回内容匹配，全链路链路持久化验证通过。")

if __name__ == "__main__":
    unittest.main()
