from abc import ABC, abstractmethod

class BaseWorker(ABC):
    @abstractmethod
    async def run(self, messages: list, **kwargs) -> dict:
        """
        Worker 的执行核心。
        """
        pass
