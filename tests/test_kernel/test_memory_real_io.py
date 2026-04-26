import os
# 关键：在导入任何内核/工具模块之前，强制设定测试目录环境变量
TEST_MEMORY_DIR = "test_memory_vault"
os.environ["MEMORY_DIR"] = TEST_MEMORY_DIR

import unittest
import asyncio
import shutil
from pathlib import Path
from kernel.drivers.mcp_connect import connect_mcp

class TestMemoryRealIO(unittest.IsolatedAsyncioTestCase):
    """
    真·内存持久化集成测试。
    验证数据能否穿透 MCP 总线进入磁盘，并能被逻辑召回。
    """
    
    async def asyncSetUp(self):
        if os.path.exists(TEST_MEMORY_DIR):
            shutil.rmtree(TEST_MEMORY_DIR)
        os.makedirs(TEST_MEMORY_DIR)

    async def asyncTearDown(self):
        if os.path.exists(TEST_MEMORY_DIR):
            shutil.rmtree(TEST_MEMORY_DIR)

    async def test_mcp_memory_lifecycle(self):
        """测试：存储事实 -> 磁盘验证 -> 语义召回"""
        
        async with connect_mcp(transport="in_memory") as session:
            # 1. 存储事实
            print(f"\n📥 [Test] 正在向 {TEST_MEMORY_DIR} 写入持久化事实...")
            save_result = await session.call_tool("save_fact", {
                "title": "Quantum_Safety_Protocol",
                "content": "The quantum encryption key is stored in vault-7."
            })
            self.assertIn("✅", save_result.content[0].text)
            
            # 2. 物理检查 (现在路径应该是正确的了)
            fact_file = Path(TEST_MEMORY_DIR) / "facts" / "quantum_safety_protocol.md"
            self.assertTrue(fact_file.exists(), f"事实文件未能出现在预期路径: {fact_file}")
            
            # 3. 语义召回 (Recall)
            print("🔍 [Test] 正在通过 MCP 总线执行 Recall 召回...")
            recall_result = await session.call_tool("recall_memory", {
                "query": "encryption key"
            })
            
            recall_text = recall_result.content[0].text
            self.assertIn("vault-7", recall_text)
            self.assertIn("Source: quantum_safety_protocol.md", recall_text)
            print("✅ [OK] 内存持久化全链路验证通过 (Write -> Disk -> Read)")

if __name__ == "__main__":
    unittest.main()
