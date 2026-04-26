import httpx
import logging
from .base import BaseProvider

logger = logging.getLogger(__name__)

class OllamaProvider(BaseProvider):
    async def chat_completion(self, client: httpx.AsyncClient, payload: dict) -> dict:
        headers = {
            "Content-Type": "application/json",
        }
        # Ollama 的模型参数可能不需要前缀，这里可以进行特定的预处理
        response = await client.post(self.base_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
