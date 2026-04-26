from pathlib import Path


def register(mcp):
    """注册文件读取工具到 MCP Server

    Phase 3a: 仅支持文本文件，不限制目录范围
    后续可升级为官方 @modelcontextprotocol/server-filesystem
    """

    # 支持的文本文件扩展名
    TEXT_EXTENSIONS = {
        '.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml',
        '.toml', '.cfg', '.ini', '.csv', '.log', '.xml', '.html', '.css',
        '.sh', '.bat', '.ps1', '.java', '.c', '.cpp', '.h', '.go', '.rs',
        '.rb', '.php', '.sql', '.r', '.m', '.swift', '.kt',
    }

    @mcp.tool()
    def read_file(path: str, max_length: int = 10000) -> str:
        """读取本地文件内容。
        path: 文件路径（绝对路径或相对路径）
        max_length: 最大返回字符数，默认 10000
        支持常见文本文件格式（txt, md, py, json 等）
        """
        try:
            file_path = Path(path)

            if not file_path.exists():
                return f"错误：文件不存在: {path}"

            if not file_path.is_file():
                return f"错误：不是文件: {path}"

            suffix = file_path.suffix.lower()
            if suffix not in TEXT_EXTENSIONS and suffix != '':
                return f"错误：不支持的文件类型 '{suffix}'。支持: {', '.join(sorted(TEXT_EXTENSIONS))}"

            # 读取文件
            text = file_path.read_text(encoding="utf-8")

            # 文件信息头
            info = f"文件: {file_path.name} ({len(text)} 字符)\n{'=' * 40}\n"

            if len(text) > max_length:
                text = text[:max_length] + f"\n... (截断，共 {len(text)} 字符)"

            return info + text

        except UnicodeDecodeError:
            return f"错误：文件不是 UTF-8 编码，无法读取: {path}"
        except PermissionError:
            return f"错误：没有权限读取: {path}"
        except Exception as e:
            return f"读取错误: {e}"

    @mcp.tool()
    def list_dir(path: str = ".") -> str:
        """列出目录内容。path: 目录路径，默认当前目录"""
        try:
            dir_path = Path(path)
            if not dir_path.exists():
                return f"错误：目录不存在: {path}"
            if not dir_path.is_dir():
                return f"错误：不是目录: {path}"

            items = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name))
            lines = []
            for item in items:
                prefix = "[DIR] " if item.is_dir() else "      "
                size = f" ({item.stat().st_size} bytes)" if item.is_file() else ""
                lines.append(f"{prefix}{item.name}{size}")

            return f"目录: {dir_path.resolve()}\n共 {len(items)} 项:\n" + "\n".join(lines)

        except Exception as e:
            return f"列目录错误: {e}"
