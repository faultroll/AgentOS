import builtins
from rootfs.applets.base import BaseApplet

class LsApplet(BaseApplet):
    @property
    def name(self) -> str:
        return "ls"

    @property
    def description(self) -> str:
        return "List all applications registered in the OS Process Table"

    async def run(self, args: list[str]) -> None:
        """List registered apps from the Kernel Process Table."""
        process_table = getattr(builtins, "_os_process_table", None)
        
        if not process_table:
            print("❌ OS Process Table unavailable.")
            return

        apps = process_table.list_all()
        
        if not apps:
            print("📭 No apps registered. Check your apps/ directory and manifests.")
            return

        print("\n📋 --- Registered OS Applications ---")
        print(f"{'NAME':<18} {'VER':<8} {'DESCRIPTION'}")
        print("-" * 60)
        
        for proc in sorted(apps, key=lambda x: x.name):
            manifest = proc.manifest
            desc = (manifest.description[:40] + "...") if len(manifest.description) > 40 else manifest.description
            print(f"{proc.name:<18} {manifest.version:<8} {desc}")
        
        print("-" * 60)
        print(f"Total: {len(apps)} apps registered.\n")
