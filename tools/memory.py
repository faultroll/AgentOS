import os
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

def register(mcp, base_dir: str = None):
    """
    Register the persistent Markdown memory tool to the MCP server.
    
    If base_dir is provided, it scopes the memory to that directory.
    Otherwise, it defaults to the OS-level global memory dir.
    """

    def _get_base_dir() -> Path:
        if base_dir:
            return Path(base_dir)
        import config
        return Path(config.MEMORY_DIR)

    def _ensure_dirs():
        base = _get_base_dir()
        for sub in ["facts", "preferences", "summaries"]:
            (base / sub).mkdir(parents=True, exist_ok=True)

    @mcp.tool()
    def list_facts() -> str:
        """List all persistent facts in the facts/ directory"""
        _ensure_dirs()
        facts_dir = _get_base_dir() / "facts"
        files = list(facts_dir.glob("*.md"))
        if not files:
            return "No facts found."
        return "Discovered persistent facts:\n" + "\n".join([f"- {f.name}" for f in files])

    @mcp.tool()
    def save_fact(title: str, content: str) -> str:
        """
        Persist an important fact.
        title: Short title of the fact
        content: Detailed content
        """
        _ensure_dirs()
        safe_title = "".join([c if c.isalnum() or c in "-_" else "_" for c in title])
        file_path = _get_base_dir() / "facts" / f"{safe_title.lower()}.md"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md_text = f"# {title}\n\n- **Created**: {timestamp}\n\n---\n\n{content}\n"
        
        file_path.write_text(md_text, encoding="utf-8")
        logger.info(f"🧠 [MCP Memory] Fact saved: {file_path}")
        return f"✅ Fact successfully persisted to storage: {file_path.name}"

    @mcp.tool()
    def recall_memory(query: str) -> str:
        """
        Search persistent memory (facts/summaries) for keywords.
        """
        _ensure_dirs()
        base = _get_base_dir()
        keywords = [kw.lower() for kw in query.split() if len(kw) > 1]
        
        results = []
        for file_path in base.rglob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                if any(kw in content.lower() for kw in keywords) or any(kw in file_path.name.lower() for kw in keywords):
                    results.append(f"### Source: {file_path.name}\n{content}")
            except Exception as e:
                logger.error(f"Failed to read memory file {file_path}: {e}")
                
        if not results:
            return "No relevant persistent memory retrieved."
        return "\n\n".join(results)

    @mcp.tool()
    async def govern_context(messages_json: str, os_signal: str = None) -> str:
        """
        [GOVERNANCE] 执行上下文治理。
        根据信号和对话长度，自动决定是否执行认知压缩，并确保语义连贯。
        返回治理后的 messages 列表 JSON。
        """
        try:
            messages = json.loads(messages_json)
        except:
            return messages_json

        # 治理阈值 (硬编码在工具层，也可通过配置下发)
        MIN_COMPRESSION_THRESHOLD = 3
        
        # 1. 信号与阈值校验
        if not os_signal or os_signal not in ("CONTEXT_PRESSURE", "CONTEXT_OVERFLOW"):
            return messages_json
            
        if len(messages) < MIN_COMPRESSION_THRESHOLD:
            logger.info("🛡️ [MMU] History too short for meaningful compression. Skipping.")
            return messages_json

        # 2. 执行总结 (复用 L2 总结逻辑或直接调用 LLM)
        summary_info = await summarize_context(messages_json)
        # 提取摘要文本（简单解析，实际生产需更严谨）
        summary_text = summary_info.split("摘要内容：\n")[-1]

        # 3. 语义打捞与物理缝合 (Governance Engine v2)
        # 强制保留 System [0] 和 Tail [Last 2]
        current_tail = list(messages[-2:])
        
        # 语义底线：确保包含至少一个 User 意图
        if not any(m["role"] == "user" for m in current_tail):
            user_msgs = [m for m in messages if m["role"] == "user"]
            if user_msgs:
                current_tail.insert(0, user_msgs[-1])
        
        # 构造治理后的消息序列
        governed_messages = [messages[0]] # System
        governed_messages.append({"role": "assistant", "content": f"系统通知：对话已治理。核心纪要如下：\n\n{summary_text}"})
        
        for msg in current_tail:
            if msg not in governed_messages:
                governed_messages.append(msg)

        logger.info(f"✅ [MMU] Context governed: {len(messages)} -> {len(governed_messages)}.")
        return json.dumps(governed_messages, ensure_ascii=False)

    @mcp.tool()
    async def summarize_context(messages_json: str) -> str:
        """
        [L2 Memory] 压缩当前上下文。建议在触发 CONTEXT_PRESSURE 信号时调用。
        messages_json: 原始消息序列的 JSON 字符串
        """
        from kernel.compute.router import call_llm
        import builtins
        
        # 核心加固：获取 OS 运行时的全局调度器句柄
        scheduler = getattr(builtins, "_os_scheduler", None)

        try:
            messages = json.loads(messages_json)
        except:
            return "Error: Invalid messages_json format."

        prompt = (
            "你是一个记忆整理专家。请将以下对话历史压缩成一个精炼的 Markdown 摘要。\n"
            "要求：1. 保留关键事实和决定。2. 忽略琐碎的寒暄。3. 保持客观。\n"
            "输出格式：# 会话摘要\n\n- **核心进展**：...\n- **待办事项**：..."
        )

        logger.info("🧠 [Memory Tool] Requesting cheap model for summarization...")
        
        # 核心策略：申请廉价算力 (Cost-First Strategy)
        models = scheduler.select_model(strategy="cost", cost_limit="free") if scheduler else None
        
        response = await call_llm(
            messages=[{"role": "user", "content": f"对话内容：\n{json.dumps(messages[-10:], ensure_ascii=False)}"}],
            system_prompt=prompt,
            models_to_try=models,
            app_name="system.tool.memory"
        )

        summary = response["choices"][0]["message"]["content"]
        
        # 持久化到 L2 存储
        _ensure_dirs()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        file_path = _get_base_dir() / "summaries" / f"summary_{timestamp}.md"
        file_path.write_text(summary, encoding="utf-8")
        
        return f"✅ 上下文已压缩并存储至 L2 记忆：{file_path.name}\n\n摘要内容：\n{summary}"
