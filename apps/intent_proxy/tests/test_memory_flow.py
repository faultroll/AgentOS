import unittest
import os
import shutil
import logging
import builtins
import asyncio
import json
import time
from unittest.mock import patch

import config
import kernel.compute.router as router
from kernel.compute.scheduler import ComputeScheduler, ModelProfile
from kernel.telemetry import global_telemetry
from kernel.state import create_process
from apps.intent_proxy.app import intent_proxy_app
from tests.test_kernel.helpers import FakeProvider

# 统一日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MemoryFlowWar")

TEST_MEM_DIR = "test_memory_war_vault"

class TestRealMemoryFlow(unittest.IsolatedAsyncioTestCase):
    """
    AgentOS 记忆增强实战演习 (Hardened v2)
    验证：L1 -> L2 -> L3 全链路物理对流
    """

    async def asyncSetUp(self):
        # [1] 环境隔离
        if os.path.exists(TEST_MEM_DIR):
            shutil.rmtree(TEST_MEM_DIR)
        os.makedirs(TEST_MEM_DIR)
        self.old_mem_dir = config.MEMORY_DIR
        config.MEMORY_DIR = TEST_MEM_DIR
        
        # [2] 物理全劫持：让所有驱动名都指向我们的 FakeProvider
        self.old_instances = router.PROVIDER_INSTANCES.copy()
        router.PROVIDER_INSTANCES.clear()
        
        self.p_fake = FakeProvider("p_fake")
        # 劫持所有 config 中定义的驱动
        all_providers = set(config.ROUTER_CONFIG.values())
        for p_name in all_providers:
            router.PROVIDER_INSTANCES[p_name] = self.p_fake

        # [3] 注入调度器
        self.test_bus = global_telemetry
        self.test_bus._events.clear()
        self.test_bus._model_stats.clear()
        self.scheduler = ComputeScheduler(telemetry=self.test_bus)
        
        # 注册 config 中的所有模型到调度器，确保它能 select 出来
        for model in config.ROUTER_MODELS:
            self.scheduler.register_model(ModelProfile(
                alias=model,
                provider=config.ROUTER_CONFIG.get(model, "unknown")
            ))
        builtins._os_scheduler = self.scheduler

    async def asyncTearDown(self):
        router.PROVIDER_INSTANCES.clear()
        router.PROVIDER_INSTANCES.update(self.old_instances)
        config.MEMORY_DIR = self.old_mem_dir
        if os.path.exists(TEST_MEM_DIR):
            shutil.rmtree(TEST_MEM_DIR)
        if hasattr(builtins, "_os_scheduler"):
            del builtins._os_scheduler

    async def test_triple_layer_memory_convection(self):
        """
        全生命周期验证。
        """
        logger.info("\n--- ⚔️ 开始记忆对流实战演习 ---")

        # [Phase 1: L2 压力压缩]
        logger.info("📡 Step 1: 模拟对话压力...")
        
        # 准备总结核心返回
        self.p_fake.response_data = {
            "choices": [{"message": {"role": "assistant", "content": "# L2 Summary\nUser is Antigravity."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10}
        }
        
        state = create_process("Who am I?")
        state["os_signal"] = "CONTEXT_PRESSURE"
        # 注入 8 条对话历史，确保超过压缩阈值 (6)
        state["messages"] = [
            {"role": "system", "content": "System Boot"},
            {"role": "user", "content": "Name: A"}, {"role": "assistant", "content": "Ok"},
            {"role": "user", "content": "Age: 20"}, {"role": "assistant", "content": "Ok"},
            {"role": "user", "content": "Job: Pilot"}, {"role": "assistant", "content": "Ok"},
            {"role": "user", "content": "Identity: Antigravity"},
            {"role": "assistant", "content": "Hello Antigravity."}
        ]

        # 运行
        final_state = await intent_proxy_app.ainvoke(state)
        
        # [Assert Phase 1: 语义化校验]
        msg_len = len(final_state["messages"])
        logger.info(f"📊 Compression Result: {len(state['messages'])} -> {msg_len}")
        
        # 1. 验证治理的正向性 (长度必须减少)
        self.assertLess(msg_len, len(state["messages"]), "治理失败：压缩后长度未减少")
        
        # 2. 验证特征完整性 (必须包含总结说明)
        all_content = "".join([m["content"] for m in final_state["messages"]])
        self.assertIn("核心纪要", all_content, "治理失败：未发现 L2 摘要标识")
        
        # 3. 验证语义链完整性 (必须包含 User 消息供 Recall 使用)
        has_user = any(m["role"] == "user" for m in final_state["messages"])
        self.assertTrue(has_user, "治理失败：User 意图丢失，Recall 节点将崩溃")
        
        logger.info("✅ L2 治理语义验证通过。")

        # [Phase 2: L3 事实沉淀]
        logger.info("📡 Step 2: 模拟架构师反思并沉淀...")
        
        # 准备架构师返回：包含持久化标签
        self.p_fake.response_data = {
            "choices": [{"message": {
                "role": "assistant", 
                "content": "<thought>Distilling: [PERSIST]: User_Name | Antigravity</thought><blueprint>Confirmed</blueprint>"
            }}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10}
        }
        
        # 再次 invoke (模拟下一轮对话或当前轮的后续流转)
        # 注意：memory_reflect_node 通常在节点链中
        state_with_fact = await intent_proxy_app.ainvoke(final_state)
        
        fact_file = os.path.join(TEST_MEM_DIR, "facts", "user_name.md")
        self.assertTrue(os.path.exists(fact_file), "L3 沉淀失败。")
        logger.info("✅ L3 事实落盘验证通过。")

        # [Phase 3: 重生加载]
        logger.info("📡 Step 3: 新会话加载验证...")
        
        # 模拟模型正常回复
        self.p_fake.response_data = {
            "choices": [{"message": {"role": "assistant", "content": "I remember you."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10}
        }
        
        new_state = create_process("Who am I?")
        post_state = await intent_proxy_app.ainvoke(new_state)
        
        app_state = post_state.get("app_state", {})
        memory = str(app_state.get("relevant_memory", []))
        self.assertIn("Antigravity", memory)
        logger.info("✅ 最终全链路：大满贯通过！")

if __name__ == "__main__":
    unittest.main()
