import httpx
from kernel.compute.providers.base import BaseProvider

class FakeProvider(BaseProvider):
    """
    A fake provider for testing the Router without network calls.
    Allows pre-configuring responses or errors.
    """
    def __init__(self, name: str, behavior="success", response_data=None):
        super().__init__(name, "http://fake", "fake-key")
        self.behavior = behavior
        self.response_data = response_data or {
            "choices": [{"message": {"role": "assistant", "content": "Fake response"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.0}
        }
        self.call_count = 0

    async def chat_completion(self, client: httpx.AsyncClient, payload: dict) -> dict:
        self.call_count += 1
        if self.behavior == "success":
            return self.response_data
        elif self.behavior == "429":
            raise httpx.HTTPStatusError("Rate limit", request=None, response=httpx.Response(429, content=b"Rate limit"))
        elif self.behavior == "500":
            raise httpx.HTTPStatusError("Internal Error", request=None, response=httpx.Response(500, content=b"Internal Error"))
        elif self.behavior == "timeout":
            raise httpx.TimeoutException("Timeout")
        else:
            raise Exception(f"Unknown behavior: {self.behavior}")
