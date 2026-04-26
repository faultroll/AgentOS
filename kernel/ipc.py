"""AgentOS Kernel — Inter-Process Communication (Mailbox)

Provides async message passing between Apps.
Design principles:
  - Pull-based (not push) — Apps check their mailbox when THEY choose to,
    preventing external injection from disrupting agent execution.
  - Opaque messages — OS delivers but never inspects content.
  - v3 skeleton — actual IPC logic activates when a second App needs it.
"""
import logging
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class IPCMessage:
    """A message in the mailbox."""
    from_app: str
    to_app: str
    payload: dict
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            import time
            self.timestamp = time.time()


class Mailbox:
    """Async mailbox IPC — OS-provided communication primitive."""

    def __init__(self):
        self._boxes: dict[str, asyncio.Queue] = defaultdict(lambda: asyncio.Queue())

    async def send(self, from_app: str, to_app: str, payload: dict) -> None:
        """Deliver a message to the target App's inbox."""
        msg = IPCMessage(from_app=from_app, to_app=to_app, payload=payload)
        await self._boxes[to_app].put(msg)
        logger.info(f"📬 [Kernel/IPC] Message: {from_app} → {to_app}")

    async def receive(self, app_name: str, timeout: float = 0.0) -> Optional[IPCMessage]:
        """
        App pulls a message from its own inbox.
        Returns None if no message available within timeout.
        """
        try:
            if timeout > 0:
                return await asyncio.wait_for(
                    self._boxes[app_name].get(), timeout=timeout
                )
            else:
                return self._boxes[app_name].get_nowait()
        except (asyncio.TimeoutError, asyncio.QueueEmpty):
            return None

    def peek(self, app_name: str) -> int:
        """Return the number of unread messages for an App."""
        return self._boxes[app_name].qsize()
