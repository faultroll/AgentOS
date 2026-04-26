# ====================== AgentOS v3 Configuration ======================
# OS-level configuration ONLY. App-specific config lives in manifest.yaml.
import os
from dotenv import load_dotenv

load_dotenv()

# --- MCP Transport ---
MCP_TRANSPORT = "in_memory"

# --- Debug ---
DEBUG_MODE = True

# --- Paths ---
MEMORY_DIR = os.getenv("MEMORY_DIR", "memory")
APPS_DIR = os.getenv("APPS_DIR", "apps")

# --- Hub Gateway / Interceptor ---
HUB_HOST = os.getenv("HUB_HOST", "0.0.0.0")
HUB_PORT = int(os.getenv("HUB_PORT", 8001))
DEFAULT_APP = os.getenv("DEFAULT_APP", "intent-proxy")

# --- STDIO MCP Servers (for stdio transport mode) ---
STDIO_SERVERS = {
    # "memory": {
    #     "command": "npx",
    #     "args": ["-y", "@modelcontextprotocol/server-memory"],
    # },
}

# ====================== Provider Definitions (OS-level) ======================

PROVIDERS = {
    "local_engine": {
        "base_url": "http://localhost:11434/v1/chat/completions",
        "api_key": "not-needed",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1/chat/completions",
        "api_key": "ollama",
    },
}

# ====================== Model Registry (OS-level pool) ======================
# The Scheduler uses this as its "CPU pool".
# Format: { "model_alias": "provider_name" }

ROUTER_CONFIG = {
    "architect-local": "local_engine",
    "qwen/qwen3-coder:free": "openrouter",
    "tencent/hy3-preview:free": "openrouter",
    "google/gemma-4-26b-a4b-it:free": "openrouter",
    "nvidia/nemotron-3-super-120b-a12b:free": "openrouter",
    "qwen2.5-coder:7b": "ollama",
}

# Priority sequence (first = highest priority)
ROUTER_MODELS = [
    "architect-local",
    "tencent/hy3-preview:free",
    "qwen/qwen3-coder:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-26b-a4b-it:free",
    "qwen2.5-coder:7b",
]
