"""AgentOS Kernel — Compute Router (Executor)

The Router EXECUTES LLM calls. It does NOT decide which model to use.
Model selection is the Scheduler's job.

The Router:
  1. Receives an ordered list of models to try (from Scheduler)
  2. Sends the request to the appropriate Provider
  3. Handles fallback on failure
  4. Emits TelemetryEvents for every attempt
"""
import time
import httpx
import logging
from typing import Optional

from config import PROVIDERS
from kernel.telemetry import TelemetryBus
from .providers.openrouter import OpenRouterProvider
from .providers.ollama import OllamaProvider

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# --- Provider instance pool ---
def _init_providers() -> dict:
    instances = {}
    for p_name, p_config in PROVIDERS.items():
        if p_name == "openrouter":
            instances[p_name] = OpenRouterProvider(p_name, p_config["base_url"], p_config["api_key"])
        elif p_name == "ollama":
            instances[p_name] = OllamaProvider(p_name, p_config["base_url"], p_config["api_key"])
        elif p_name == "local_engine":
            instances[p_name] = OllamaProvider(p_name, p_config["base_url"], p_config["api_key"])
    return instances


PROVIDER_INSTANCES = _init_providers()


async def call_llm(
    messages: list,
    system_prompt: str = None,
    tools: list = None,
    models_to_try: list[str] = None,
    router_config: dict = None,
    telemetry: TelemetryBus = None,
    app_name: str = "unknown",
) -> dict:
    """
    Execute an LLM call against the given model sequence.

    Args:
        messages: Conversation messages
        system_prompt: Optional system prompt to prepend
        tools: Optional tool definitions
        models_to_try: Ordered list of model aliases (from Scheduler)
        router_config: Model-to-provider mapping (from config)
        telemetry: TelemetryBus for event emission
        app_name: Which App is making this call (for telemetry)
    """
    from config import ROUTER_CONFIG, ROUTER_MODELS, MODEL_METADATA
    from kernel.telemetry import global_telemetry
    from kernel.compute.scheduler import ComputeScheduler

    # Fallback: if no model list provided, use full config sequence
    if not models_to_try:
        models_to_try = ROUTER_MODELS
    if not router_config:
        router_config = ROUTER_CONFIG
    
    if telemetry is None:
        telemetry = global_telemetry

    # Initialize a temporary scheduler or use global registry
    # In a real OS, this would be a persistent kernel service
    scheduler = ComputeScheduler(telemetry=telemetry)
    scheduler.register_from_config(router_config or ROUTER_CONFIG, ROUTER_MODELS, MODEL_METADATA)

    payload_messages = []
    if system_prompt:
        payload_messages.append({"role": "system", "content": system_prompt})
    payload_messages.extend(messages)

    total_chars = sum(len(str(m.get("content", ""))) for m in payload_messages)
    estimated_tokens = int(total_chars / 3.5)
    
    # [REFINED] Best-effort: Try to find the best core, but NEVER skip all.
    if not models_to_try:
        models_to_try = scheduler.select_model(estimated_tokens=estimated_tokens)
    
    # If scheduler still returns empty (unlikely with our penalty logic), 
    # fallback to the hardcoded list to ensure WE AT LEAST TRY.
    if not models_to_try:
        models_to_try = ROUTER_MODELS
    
    logger.debug(f"📊 [Router] Task Size: ~{estimated_tokens} tokens | Sequence: {models_to_try}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        for model_alias in models_to_try:
            provider_name = router_config.get(model_alias)
            provider = PROVIDER_INSTANCES.get(provider_name)

            if not provider:
                logger.warning(
                    f"⚠️ [Router] No provider for {model_alias} "
                    f"(mapped to: {provider_name}), skipping"
                )
                continue

            payload = {"model": model_alias, "messages": payload_messages}
            if tools:
                payload["tools"] = tools

            logger.info(f"🔄 [Router] → Provider: {provider.name} | Model: {model_alias}")

            start_time = time.time()
            try:
                data = await provider.chat_completion(client, payload)
                elapsed_ms = (time.time() - start_time) * 1000

                # Extract usage info
                usage = data.get("usage", {})
                cost = float(usage.get("cost", 0.0))
                token_in = usage.get("prompt_tokens", 0)
                token_out = usage.get("completion_tokens", 0)

                choices = data.get("choices", [])
                message_content = choices[0].get("message", {}).get("content", "") if choices else ""
                content_len = len(message_content)
                
                # [REFINED] Physical Signal Injection
                # We report signals EVEN IF successful, to let App decide on compression.
                meta = MODEL_METADATA.get(model_alias, {})
                model_limit = meta.get("context_window", 8192)
                
                finish_reason = choices[0].get("finish_reason") if choices else None
                
                if finish_reason == "length" or estimated_tokens > model_limit:
                    logger.warning(f"⚠️ [Router] {model_alias} overflow detected (OVERFLOW)")
                    data["os_signal"] = "CONTEXT_OVERFLOW"
                elif estimated_tokens > model_limit * 0.8:
                    logger.info(f"💡 [Router] {model_alias} under pressure (PRESSURE)")
                    data["os_signal"] = "CONTEXT_PRESSURE"

                # Billing guard
                if cost > 0.0:
                    logger.warning(f"🚨 [Router] Non-free cost detected: ${cost}")
                else:
                    logger.info(f"✅ [Router] OK (provider={provider.name}, len={content_len}, {elapsed_ms:.0f}ms)")
                
                # Emit telemetry
                if telemetry:
                    telemetry.emit_llm_call(
                        app_name=app_name,
                        model_alias=model_alias,
                        provider=provider.name,
                        latency_ms=elapsed_ms,
                        token_input=token_in,
                        token_output=token_out,
                        success=True,
                        cost=cost,
                    )

                return data

            except httpx.HTTPStatusError as e:
                elapsed_ms = (time.time() - start_time) * 1000
                error_type = str(e.response.status_code)
                if e.response.status_code == 429:
                    logger.warning(f"⚠️ [Router] {provider.name} rate-limited (429), fallback...")
                else:
                    logger.error(f"❌ [Router] {provider.name} HTTP {e.response.status_code}")

                if telemetry:
                    telemetry.emit_llm_call(
                        app_name=app_name,
                        model_alias=model_alias,
                        provider=provider.name,
                        latency_ms=elapsed_ms,
                        token_input=0, token_output=0,
                        success=False,
                        error_type=error_type,
                    )
                continue

            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(f"❌ [Router] {provider.name} error: {str(e)}")

                if telemetry:
                    telemetry.emit_llm_call(
                        app_name=app_name,
                        model_alias=model_alias,
                        provider=provider.name,
                        latency_ms=elapsed_ms,
                        token_input=0, token_output=0,
                        success=False,
                        error_type=type(e).__name__,
                    )
                continue

    # All attempts failed
    error_msg = "All providers and models in router failed to deliver service."
    logger.error(f"💀 [Router] {error_msg}")
    return {"choices": [{"message": {"role": "assistant", "content": f"Error: {error_msg}"}}]}
