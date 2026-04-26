import asyncio
import builtins
from kernel.state import create_process
from rootfs.applets.base import BaseApplet

class EvalApplet(BaseApplet):
    @property
    def name(self) -> str:
        return "eval"

    @property
    def description(self) -> str:
        return "Run the Evaluator service manually"

    async def run(self, args: list[str]) -> None:
        """Run Evaluator service from the shell via Kernel-Process Table."""
        process_table = getattr(builtins, "_os_process_table", None)
        
        if not process_table:
            print("❌ OS Process Table unavailable.")
            return

        proc = process_table.get("evaluator")
        if not proc:
            print("❌ Evaluator App (evaluator) is not registered in the OS.")
            return

        try:
            # Blindness Principle: We don't ask about files, we ask the Kernel for the object.
            builder = proc.instantiate()
            agent = builder() if callable(builder) else builder
        except Exception as e:
            print(f"❌ Failed to boot Evaluator: {e}")
            return

        if not agent:
            print("❌ Evaluator agent instance could not be created.")
            return

        print("🚀 Running system evaluation (LLM-as-Judge)...")
        inputs = create_process("Evaluate System", app_name="evaluator")
        
        final_state = await agent.ainvoke(inputs)
        result = final_state.get("app_state", {}).get("final_response")
        print(f"\n✅ Evaluator Result:\n{result}")
