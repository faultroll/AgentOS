"""AgentOS Kernel — Process Manager

Manages App process lifecycle: creation, lookup, and teardown.
Each App declared in apps/*/manifest.yaml gets a process entry.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class AppManifest:
    """Parsed content of an App's manifest.yaml."""
    name: str
    version: str = "0.0.0"
    description: str = ""
    tools: list[str] = field(default_factory=list)
    compute: dict = field(default_factory=dict)
    memory_config: dict = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "AppManifest":
        """Load manifest from a YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(
            name=data.get("name", path.parent.name),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            tools=data.get("tools", []),
            compute=data.get("compute", {}),
            memory_config=data.get("memory", {}),
        )


@dataclass
class AppProcess:
    """A running App process."""
    manifest: AppManifest
    app_dir: Path
    status: str = "ready"  # ready | running | stopped

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def prompts_dir(self) -> Path:
        return self.app_dir / "prompts"

    @property
    def memory_dir(self) -> Path:
        return self.app_dir / "memory"

    def instantiate(self):
        """
        [Kernel Hook] Instantiate the application agent.
        This encapsulates the Physical-to-Logic mapping.
        """
        import importlib
        import inspect
        
        module_name = f"apps.{self.app_dir.name.replace('-', '_')}.app"
        try:
            module = importlib.import_module(module_name)
            # Support both 'build_app(session=...)' and direct object
            builder_fn = getattr(module, "build_app", getattr(module, f"build_{self.app_dir.name.replace('-', '_')}_app", None))
            
            if builder_fn:
                # We return the logic handle, the caller (Rootfs) just uses it
                return builder_fn
            
            return getattr(module, f"{self.app_dir.name.replace('-', '_')}_app", None)
        except Exception as e:
            raise RuntimeError(f"Kernel failed to instantiate app {self.name}: {e}")


class ProcessTable:
    """Global process table — registry of all loaded Apps."""

    def __init__(self):
        self._processes: dict[str, AppProcess] = {}

    def register(self, process: AppProcess) -> None:
        """Register an App process."""
        self._processes[process.name] = process
        logger.info(f"📋 [Kernel/Process] Registered app: {process.name}")

    def get(self, name: str) -> Optional[AppProcess]:
        """Look up an App by name."""
        return self._processes.get(name)

    def list_all(self) -> list[AppProcess]:
        """List all registered processes."""
        return list(self._processes.values())

    def scan_and_load(self, apps_root: Path) -> None:
        """Scan the apps/ directory and load all manifest.yaml."""
        if not apps_root.is_dir():
            logger.warning(f"⚠️ [Kernel/Process] Apps directory not found: {apps_root}")
            return

        for child in sorted(apps_root.iterdir()):
            manifest_path = child / "manifest.yaml"
            if child.is_dir() and manifest_path.exists():
                try:
                    manifest = AppManifest.from_yaml(manifest_path)
                    proc = AppProcess(manifest=manifest, app_dir=child)
                    self.register(proc)
                except Exception as e:
                    logger.error(f"❌ [Kernel/Process] Failed to load {manifest_path}: {e}")
