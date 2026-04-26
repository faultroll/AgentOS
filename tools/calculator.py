def register(mcp):
    """注册计算器工具到 MCP Server"""

    @mcp.tool()
    def calculator(num1: float, num2: float, op: str) -> str:
        """简单计算器。参数: num1 (数字), num2 (数字), op (操作符: +, -, *, /)"""
        try:
            if op == "+": return str(num1 + num2)
            if op == "-": return str(num1 - num2)
            if op == "*": return str(num1 * num2)
            if op == "/": return str(num1 / num2)
            return "不支持的运算符，请使用 +, -, *, /"
        except ZeroDivisionError:
            return "错误：除数不能为零"
        except Exception as e:
            return f"计算错误: {e}"
