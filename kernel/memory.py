"""AgentOS Kernel — Memory Manager

Provides scoped memory isolation for Apps.
Three levels:
  - Global:    OS-wide facts (read-only for apps)
  - App:       Per-app persistent storage (read-write within app)
  - Ephemeral: In-memory only, dies with the process
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class MemoryManager:
    """OS-level memory scope manager."""

    def __init__(self, os_root: Path):
        self._os_root = os_root
        self._global_dir = os_root / "memory" / "global"

    def ensure_global(self) -> None:
        """Ensure the global memory directory exists."""
        self._global_dir.mkdir(parents=True, exist_ok=True)

    def create_app_scope(self, app_name: str, app_dir: Path) -> Path:
        """Create and return the memory directory for an App."""
        mem_dir = app_dir / "memory"
        for sub in ["facts", "summaries", "preferences"]:
            (mem_dir / sub).mkdir(parents=True, exist_ok=True)
        logger.info(f"🗄️ [Kernel/Memory] Scope created for app: {app_name}")
        return mem_dir

    def get_global_dir(self) -> Path:
        """Return the OS global memory path (read-only for apps)."""
        return self._global_dir

    def get_read_paths(self, app_dir: Path) -> list[Path]:
        """
        Return all paths an App is allowed to READ from.
        Includes: global memory + app's own memory.
        """
        paths = []
        if self._global_dir.exists():
            paths.append(self._global_dir)
        app_mem = app_dir / "memory"
        if app_mem.exists():
            paths.append(app_mem)
        return paths

    def get_write_path(self, app_dir: Path) -> Optional[Path]:
        """
        Return the path an App is allowed to WRITE to.
        Apps can only write to their own memory scope.
        """
        app_mem = app_dir / "memory"
        if app_mem.exists():
            return app_mem
        return None
