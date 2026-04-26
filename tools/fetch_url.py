import re
import requests


def register(mcp):
    """注册网页抓取工具到 MCP Server

    零额外依赖：用已有的 requests + 正则去 HTML 标签
    后续可升级为官方 @modelcontextprotocol/server-fetch
    """

    def _strip_html(html: str) -> str:
        """简单去除 HTML 标签，提取纯文本"""
        # 去除 script 和 style 块
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # 去除所有 HTML 标签
        text = re.sub(r'<[^>]+>', ' ', text)
        # 解码常见 HTML 实体
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
        # 压缩空白
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @mcp.tool()
    def fetch_url(url: str, max_length: int = 5000) -> str:
        """抓取指定 URL 的网页文本内容。
        url: 完整的网页地址（含 http/https）
        max_length: 最大返回字符数，默认 5000
        """
        try:
            resp = requests.get(
                url,
                timeout=10,
                headers={"User-Agent": "AgentOS/1.0 (MCP Tool)"},
            )
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")
            if "text/html" in content_type:
                text = _strip_html(resp.text)
            else:
                text = resp.text

            if len(text) > max_length:
                text = text[:max_length] + f"\n... (截断，共 {len(resp.text)} 字符)"
            return text

        except requests.exceptions.Timeout:
            return f"错误：请求超时（10秒），URL: {url}"
        except requests.exceptions.ConnectionError:
            return f"错误：无法连接到 {url}"
        except requests.exceptions.HTTPError as e:
            return f"错误：HTTP {e.response.status_code}，URL: {url}"
        except Exception as e:
            return f"抓取错误: {e}"
