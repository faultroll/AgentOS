import asyncio
import logging
import uvicorn
import builtins
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from rootfs.applets.base import BaseApplet
from config import HUB_HOST, HUB_PORT, DEFAULT_APP
from kernel.compute.router import call_llm

logger = logging.getLogger(__name__)

# FastAPI application structure - The "PC-Wide Interceptor Proxy"
# Following the Blindness Principle: This hub is agnostic of specific Apps.
app = FastAPI(title="AgentOS Universal Interceptor Proxy")

@app.get("/v1/models")
async def list_models():
    """
    Disguise as a Provider: List available models from the Kernel Scheduler.
    Following the Blindness Principle: We list kernels models, not Apps.
    """
    scheduler = getattr(builtins, "_os_scheduler", None)
    if not scheduler:
        return JSONResponse({"data": []})
    
    models = []
    # Scheduler keeps the source of truth for what can be computed
    for alias in scheduler._models.keys():
        models.append({
            "id": alias,
            "object": "model",
            "owned_by": "agentos-kernel"
        })
    return JSONResponse({"object": "list", "data": models})

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    Universal Proxy & Interceptor:
    Listens for all local AI requests and routes them through the OS Kernel.
    """
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    messages = data.get("messages", [])
    model = data.get("model", "")

    # Implementation of the "Blindness Principle":
    # 1. We don't try to load apps.
    # 2. We don't try to find app files.
    # 3. We simply treat the 'model' or 'app_name' as a routing hint for the Kernel Router.
    
    source = "Explicit Hijack" if ":" in model else "Implicit Proxy"
    app_tag = model.split(":", 1)[0] if ":" in model else DEFAULT_APP
    actual_model = model.split(":", 1)[1] if ":" in model else model

    logger.info(f"\n[Hub] Intercepted {source} | Tag: {app_tag} | Model: {actual_model}")

    # Use the Scheduler to resolve the target model into a prioritized list of candidates.
    scheduler = getattr(builtins, "_os_scheduler", None)
    if scheduler:
        models = scheduler.select_model(force_model=actual_model)
    else:
        models = [actual_model] if actual_model else None

    from config import DEBUG_MODE
    if DEBUG_MODE:
        user_msg = messages[-1]["content"] if messages else ""
        print(f"\n[Hub/DEBUG] 📥 Proxy Input:\n{user_msg}")

    # Telemetry and Routing are handled by the Kernel Router.
    try:
        response_data = await call_llm(
            messages=messages,
            app_name=f"os.hub.{app_tag}",
            models_to_try=models
        )

        if DEBUG_MODE:
            choices = response_data.get("choices", [])
            content = choices[0].get("message", {}).get("content", "") if choices else ""
            print(f"[Hub/DEBUG] 📤 Proxy Output:\n{content}\n")

        return JSONResponse(content=response_data)
    except Exception as e:
        logger.error(f"[Hub] Execution error: {e}")
        return JSONResponse({
            "error": "OS Execution Failed",
            "message": str(e)
        }, status_code=500)


class GatewayApplet(BaseApplet):
    _api_task = None
    _server_instance = None

    @property
    def name(self) -> str:
        return "gateway"

    @property
    def description(self) -> str:
        return f"Universal AI Proxy Hub (Host: {HUB_HOST}, Port: {HUB_PORT})"

    async def run(self, args: list[str]) -> None:
        if not args:
            print("Usage: gateway [start|stop]")
            return
            
        action = args[0]
        
        if action == "start":
            if self._api_task and not self._api_task.done():
                print("⚠️ Hub is already running.")
                return
                
            print(f"🚀 Starting Hub on {HUB_HOST}:{HUB_PORT} | Blindness Mode: ON")
            config = uvicorn.Config(app, host=HUB_HOST, port=HUB_PORT, log_level="warning")
            self._server_instance = uvicorn.Server(config)
            self._server_instance.install_signal_handlers = lambda: None
            
            self._api_task = asyncio.create_task(self._server_instance.serve())
            await asyncio.sleep(0.5)
            print("✅ Hub Online. Disguised as a standard Provider.")
            
        elif action == "stop":
            if self._server_instance:
                print("🛑 Stopping Hub...")
                self._server_instance.should_exit = True
                if self._api_task:
                    await self._api_task
                self._server_instance = None
                self._api_task = None
                print("✅ Hub offline.")
            else:
                print("⚠️ Hub is not running.")
        else:
            print(f"Unknown action: {action}. Use 'start' or 'stop'.")
