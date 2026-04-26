import asyncio
import builtins
import inspect
from kernel.drivers.mcp_connect import connect_mcp
from kernel.state import create_process
from rootfs.applets.base import BaseApplet

class RunApplet(BaseApplet):
    @property
    def name(self) -> str:
        return "run"

    @property
    def description(self) -> str:
        return "Load and run an App in foreground (run <app_name>)"

    async def run(self, args: list[str]) -> None:
        if not args:
            print("Usage: run <app_name>")
            return
        
        app_name = args[0]
        process_table = getattr(builtins, "_os_process_table", None)
        if not process_table:
            print("❌ [Applet run] Process table not found.")
            return

        proc = process_table.get(app_name)
        if not proc:
            print(f"❌ App '{app_name}' not found. Verify it exists in the OS Process Table.")
            return

        try:
            # Following the Ignorance Principle: We ask the Kernel for the executable handle.
            builder_handle = proc.instantiate()
        except Exception as e:
            print(f"❌ [Applet run] Kernel failed to prepare App {app_name}: {e}")
            return

        print(f"\n🚀 Foreground App Execution: {app_name}...")
        thread_config = {"configurable": {"thread_id": f"cli_session_{app_name.replace('-', '_')}"}}
        is_first_turn = True
        
        async with connect_mcp("in_memory") as session:
            # Handle standard builder protocol (with optional session)
            if callable(builder_handle):
                sig = inspect.signature(builder_handle)
                agent = builder_handle(session=session) if "session" in sig.parameters else builder_handle()
            else:
                agent = builder_handle

            if not agent:
                print(f"❌ [Applet run] Failed to obtain agent instance for {app_name}")
                return

            while True:
                try:
                    if is_first_turn:
                        query = await asyncio.to_thread(input, f"\n[{app_name}] 请输入问题: ")
                        query = query.strip()
                        if not query: continue
                        inputs = create_process(query, app_name=app_name)
                        is_first_turn = False
                    else:
                        query = await asyncio.to_thread(input, f"\n[{app_name} 继续] (输入 exit 退出应用, 返回 rootfs): ")
                        query = query.strip()
                        if query.lower() in ('exit', 'quit'):
                            print(f"⏸️ Detaching from {app_name}...")
                            break
                        if not query: continue
                        inputs = {"messages": [{"role": "user", "content": query}]}

                    final_state = await agent.ainvoke(inputs, config=thread_config)
                    
                    # Display response
                    app_state = final_state.get("app_state", {})
                    if "final_response" in app_state:
                        response = app_state["final_response"]
                        content = response.get("choices", [{}])[0].get("message", {}).get("content", "No content") if isinstance(response, dict) else str(response)
                        print(f"\n模型回答：{content}")
                    else:
                        messages = final_state.get("messages", [])
                        last_msg = messages[-1] if messages else {}
                        answer = last_msg.get("content", "").replace("【结束】", "").strip()
                        print(f"\n模型回答：{answer}")
                    
                    if final_state.get("is_finished"):
                        print("\n[任务已完成]")
                        
                except (KeyboardInterrupt, EOFError):
                    break
