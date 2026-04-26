"""AgentOS Tool Registry

Tools are registered ON-DEMAND based on an App's manifest.
This prevents an App from using tools it didn't declare.
"""
from mcp.server.fastmcp import FastMCP
import logging

logger = logging.getLogger(__name__)

def create_mcp_server(app_name: str, allowed_tools: list[str], memory_dir: str = None) -> FastMCP:
    """Create a scoped MCP server for a specific app."""
    mcp = FastMCP(name=f"agentos_{app_name}")
    
    for tool in allowed_tools:
        if tool == "calculator":
            from tools.calculator import register
            register(mcp)
        elif tool == "echo":
            from tools.echo import register
            register(mcp)
        elif tool == "memory":
            from tools.memory import register
            register(mcp, base_dir=memory_dir)
        elif tool == "fetch_url":
            from tools.fetch_url import register
            register(mcp)
        elif tool == "read_file":
            from tools.read_file import register
            register(mcp)
        else:
            logger.warning(f"⚠️ [Tools] Unknown tool requested by {app_name}: {tool}")
            
    return mcp

# For backwards compatibility with standard fallback (like stdio external servers)
# We provide a global default server with everything if not specified.
# 核心加固：设为 None 以允许 tools.memory 动态从 config.MEMORY_DIR 读取最新路径
mcp_server = create_mcp_server("default", ["calculator", "echo", "memory", "fetch_url", "read_file"], None)
