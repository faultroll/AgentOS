def register(mcp):
    """注册回声工具到 MCP Server"""

    @mcp.tool()
    def echo(message: str) -> str:
        """回声工具，原样返回输入的消息。可用于测试 MCP 连接是否正常"""
        return message
