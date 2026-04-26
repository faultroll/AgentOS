"""AgentOS Rootfs — Busyagent Bootloader

The primary OS process. It exposes an internal shell environment.
From here, users can run applets (like API daemon) in the background,
or applications (like intent-proxy) in the foreground.
"""
import sys
import os
import asyncio
import importlib
import inspect
from pathlib import Path

# Add project root to sys.path
_OS_ROOT = Path(__file__).parent.parent
sys.path.append(str(_OS_ROOT))

from kernel.process import ProcessTable
from kernel.telemetry import global_telemetry
from kernel.compute.scheduler import ComputeScheduler
from config import ROUTER_CONFIG, ROUTER_MODELS
from rootfs.applets.base import BaseApplet

class BusyAgent:
    def __init__(self):
        self.applets: dict[str, BaseApplet] = {}
        self.registry = {}

    def load_applets(self):
        """Scan rootfs/applets for BaseApplet implementations."""
        applets_path = Path(__file__).parent / "applets"
        for file in applets_path.glob("*.py"):
            if file.name in ("__init__.py", "base.py"):
                continue
            
            module_name = f"rootfs.applets.{file.stem}"
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BaseApplet) and obj is not BaseApplet:
                        instance = obj()
                        self.applets[instance.name] = instance
                        # print(f"  [Loader] Registered applet: {instance.name}")
            except Exception as e:
                print(f"  [Loader] Failed to load {module_name}: {e}")

    async def shell_loop(self):
        print("\n AgentOS Rootfs | Busyagent (v3.2 Dynamic)")
        print("============================================================")
        print(" Welcome to the OS shell. Type 'help' for applets.")
        
        while True:
            try:
                line = await asyncio.to_thread(input, "\nAgentOS rootfs> ")
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split()
                cmd = parts[0]
                args = parts[1:]
                
                if cmd in ('exit', 'quit'):
                    print("Shutting down AgentOS...")
                    break
                    
                if cmd == 'help':
                    print("Available Applets:")
                    for name, applet in sorted(self.applets.items()):
                        print(f"  {name:<15} - {applet.description}")
                    print(f"  {'exit':<15} - Shutdown OS")
                    continue
                
                if cmd in self.applets:
                    await self.applets[cmd].run(args)
                else:
                    print(f"Unknown applet or command: {cmd}")
                
            except (KeyboardInterrupt, EOFError):
                print("\nShutting down AgentOS...")
                break
            except Exception as e:
                print(f"Shell Error: {e}")

async def boot():
    # Initialize Core Subsystems
    scheduler = ComputeScheduler(telemetry=global_telemetry)
    scheduler.register_from_config(ROUTER_CONFIG, ROUTER_MODELS)
    
    process_table = ProcessTable()
    process_table.scan_and_load(_OS_ROOT / "apps")
    
    # Store globally so applets can access it
    import builtins
    builtins._os_process_table = process_table
    builtins._os_scheduler = scheduler
    builtins._os_telemetry_bus = global_telemetry
    
    agent = BusyAgent()
    agent.load_applets()
    await agent.shell_loop()

if __name__ == "__main__":
    import logging
    # Suppress httpx info spam in shell
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # Suppress rootfs loader spam if needed
    asyncio.run(boot())
