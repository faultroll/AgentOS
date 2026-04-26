import httpx
import logging

logger = logging.getLogger(__name__)

class BaseProvider:
    def __init__(self, name: str, base_url: str, api_key: str):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key

    async def chat_completion(self, client: httpx.AsyncClient, payload: dict) -> dict:
        """
        统一的接口，供 Router 调用。
        返回标准的 OpenAI 响应 dict。
        """
        raise NotImplementedError("Subclasses must implement chat_completion")
