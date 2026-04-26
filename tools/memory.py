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
        Search persistent memory for keywords in the query.
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
