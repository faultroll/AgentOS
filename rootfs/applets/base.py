import asyncio
from abc import ABC, abstractmethod

class BaseApplet(ABC):
    """Base class for all AgentOS Applets (Busybox style)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The command name used in the shell."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A short description for the help menu."""
        pass

    @abstractmethod
    async def run(self, args: list[str]) -> None:
        """Main execution logic for the applet."""
        pass

    def get_help(self) -> str:
        """Return detailed help for this applet."""
        return f"{self.name} - {self.description}"
