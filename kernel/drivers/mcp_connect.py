"""MCP 连接工厂

根据 config.MCP_TRANSPORT 选择传输方式，返回统一的 ClientSession。
业务代码（agent loop）完全不感知传输层差异。

用法:
    async with connect_mcp() as session:
        tools = await session.list_tools()
        result = await session.call_tool("calculator", {"num1": 1, "num2": 2, "op": "+"})
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.memory import create_connected_server_and_client_session

import config
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def connect_mcp(transport: str = None):
    """创建 MCP 连接，yield ClientSession

    Args:
        transport: "in_memory" 或 "stdio"，默认取 config.MCP_TRANSPORT
    """
    transport = transport or config.MCP_TRANSPORT

    if transport == "in_memory":
        async with _connect_in_memory() as session:
            yield session

    elif transport == "stdio":
        async with _connect_stdio() as session:
            yield session

    else:
        raise ValueError(f"不支持的传输模式: {transport}，可选: in_memory, stdio")


@asynccontextmanager
async def _connect_in_memory():
    """同进程 in-memory 传输（开发/测试用）"""
    from tools import mcp_server

    async with create_connected_server_and_client_session(
        mcp_server._mcp_server
    ) as client_session:
        try:
            await client_session.initialize()
        except Exception:
            pass  # mcp 1.27.0 中可能已内部初始化
        logger.info("🔌 [MCP] Connection established (in-memory)")
        yield client_session


@asynccontextmanager
async def _connect_stdio(server_name: str = "local_agent"):
    """分进程 stdio 传输（生产/外部 MCP Server 用）"""
    server_config = config.STDIO_SERVERS.get(server_name)
    if not server_config:
        raise ValueError(f"未找到 stdio server 配置: {server_name}")

    command = server_config["command"]
    args = server_config.get("args", [])

    # 如果 command 是 "python"，替换为当前解释器路径（兼容 conda portable）
    if command == "python":
        command = sys.executable

    # 如果 args 中有相对路径的 .py 文件，转为绝对路径
    resolved_args = []
    for arg in args:
        if arg.endswith(".py") and not Path(arg).is_absolute():
            resolved_args.append(str(Path(__file__).parent / arg))
        else:
            resolved_args.append(arg)

    server_params = StdioServerParameters(command=command, args=resolved_args)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            logger.info(f"🔌 [MCP] Connection established (stdio: {server_name})")
            yield session
