import httpx
import logging
from .base import BaseProvider

logger = logging.getLogger(__name__)

class OpenRouterProvider(BaseProvider):
    async def chat_completion(self, client: httpx.AsyncClient, payload: dict) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/agentos",
            "X-Title": "AgentOS Local Harness",
        }
        
        response = await client.post(self.base_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
