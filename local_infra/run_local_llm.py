
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_REGISTRY = [
    # =========================
    # Qwen3.5 (4B / 9B / 35B-A3B)
    # =========================
    {
        "name": "Qwen3.5-4B-Q5_K_M",
        "repo": "unsloth/Qwen3.5-4B-GGUF",
        "base": "qwen3.5",
        "cmd": ["base_cmd_1"],
        "role_score": {
            "agent": 0.8,
            "chatbot": 0.8
        },
        "notes": "Small but forgetful. Good for toy chat only. Agent = nope."
    },
    {
        "name": "Qwen3.5-9B-Q4_K_M",
        "repo": "unsloth/Qwen3.5-9B-GGUF",
        "base": "qwen3.5",
        "cmd": ["base_cmd_1"],
        "role_score": {
            "agent": 0.9,
            "chatbot": 4.0
        },
        "notes": "Fast and stable. BUT tool usage is broken unless distilled."
    },
    {
        "name": "Qwopus3.5-9B-v3.Q4_K_M",
        "repo": "Jackrong/Qwopus3.5-9B-v3-GGUF",
        "base": "qwen3.5",
        "cmd": ["base_cmd_1"],
        "role_score": {
            "agent": 8.1,
            "chatbot": 7.0
        },
        "notes": "Claude-Opus distilled. Finally learns IDE tools. Strong baseline agent."
    },
    {
        "name": "Qwen3.5-9B-DeepSeek-V4-Flash-Q4_K_M",
        "repo": "Jackrong/Qwen3.5-9B-DeepSeek-V4-Flash-GGUF",
        "base": "qwen3.5",
        "cmd": ["base_cmd_1"],
        "role_score": {
            "agent": 8.0,
            "chatbot": 7.0
        },
        "notes": "Fast reasoning bias. Good speed, slightly less stable tool behavior."
    },
    {
        "name": "qwen3.5-14b-a3b-claude-4.6-opus-reasoning-distilled-reap-q2_k",
        "repo": "brunopio/Qwen3.5-14B-A3B-Claude-4.6-Opus-Reasoning-Distilled-reap-Q2_K-GGUF",
        "base": "qwen3.5",
        "cmd": ["base_cmd_1"],
        "role_score": {
            "agent": 0.0,
            "chatbot": 0.0
        },
        "notes": "Q2 is nonsense. Can run without moe in full GPU, avoiding high GPU-Copy."
    },
    {
        "name": "Qwen3.5-14B-A3B-Claude-Opus-Reasoning-Distilled-4.6-MXFP4_MOE",
        "repo": "tvall43/Qwen3.5-14B-A3B-Claude-4.6-Opus-Reasoning-Distilled-reap-gguf",
        "base": "qwen3.5",
        "cmd": [
            "base_cmd_0",
            "-c", "65536",
            "-b", "4096",
            "-ub", "1024",
            "--reasoning-budget", "1024",
            "--n-cpu-moe", "8",
            "--no-mmap",
        ],
        "role_score": {
            "agent": 5.1,
            "chatbot": 8.1
        },
        "notes": "Overall good, but a little bit slow which causes timeout when working as agent."
    },
    {
        "name": "Qwen3.5-24B-A3B-Claude-Opus-Gemini-3.1-Pro-Reasoning-Distilled-heretic.i1-Q4_K_M",
        "repo": "mradermacher/Qwen3.5-24B-A3B-Claude-Opus-Gemini-3.1-Pro-Reasoning-Distilled-heretic-i1-GGUF",
        "base": "qwen3.5",
        "cmd": ["base_cmd_1"],
        "role_score": {
            "agent": 4.1,
            "chatbot": 8.0
        },
        "notes": "Strong intelligence, BUT GPU <-> CPU swapping kills latency in IDE."
    },
    # =========================
    # Qwen3.6 (35B-A3B)
    # =========================
    {
        "name": "Qwen3.6-VL-REAP-26B-A3B-text-Q4_K_M",
        "repo": "keithnull/Qwen3.6-VL-REAP-26B-A3B-GGUF",
        "base": "qwen3.6",
        "cmd": [
            "base_cmd_1",
            "--mmproj", os.path.join(MODEL_DIR, "mmproj-REAP-26B-F16.gguf"),
            # "--temp", "0.7",
            # "--top-k", "40",
            # "--top-p", "0.95",
            # "--min-p", "0",
            # "--no-context-shift",
        ],
        "role_score": {
            "agent": 9.0,
            "chatbot": 7.1
        },
        "notes": "Multimodal. Have a try."
    },
    {
        "name": "Qwen3.6-28B-REAP20-A3B-Q4_K_M",
        "repo": "barozp/Qwen3.6-28B-REAP20-A3B-GGUF",
        "base": "qwen3.6",
        "cmd": ["base_cmd_1"],
        "role_score": {
            "agent": 4.0,
            "chatbot": 7.0
        },
        "notes": "Best balance. Less 'prompt poisoning' than 24B heretic."
    },
    {
        "name": "Qwen3.6-35B-A3B-MXFP4_MOE",
        "repo": "unsloth/Qwen3.6-35B-A3B-GGUF",
        "base": "qwen3.6",
        "cmd": ["base_cmd_1"],
        "role_score": {
            "agent": 0.8,
            "chatbot": 0.8
        },
        "notes": "Big brain but RAM eater. Feels same as Q4/IQ4 in practice."
    },
    {
        "name": "Qwen3.6-35B-A3B-uncensored-heretic-Q4_K_M",
        "repo": "llmfan46/Qwen3.6-35B-A3B-uncensored-heretic",
        "base": "qwen3.6",
        "cmd": ["base_cmd_1"],
        "role_score": {
            "agent": 0.8,
            "chatbot": 0.8
        },
        "notes": "No real gain. Just chaos + memory waste."
    },

    # =========================
    # Qwen3 (8B / 30B-A3B)
    # =========================
    {
        "name": "MiroThinker-v1.0-8B.i1-Q4_K_M",
        "repo": "mradermacher/MiroThinker-v1.0-8B-i1-GGUF",
        "base": "qwen3",
        "cmd": ["base_cmd_1"],
        "role_score": {
            "agent": 2.1,
            "chatbot": 2.0
        },
        "notes": "Reliable reasoning, but too slow for real IDE workflows."
    },
    {
        "name": "MiroThinker-v1.5-30B.i1-Q4_K_M",
        "repo": "mradermacher/MiroThinker-v1.5-30B-i1-GGUF",
        "base": "qwen3",
        "cmd": ["base_cmd_1"],
        "role_score": {
            "agent": 2.0,
            "chatbot": 2.1
        },
        "notes": "Strong reasoning, but MoE + CPU fallback = latency trap."
    },

    # =========================
    # Deepseek (16B-A2.4B)
    # =========================
    {
        "name": "DeepSeek-Coder-V2-Lite-Instruct.Q4_K_M",
        "repo": "mradermacher/DeepSeek-Coder-V2-Lite-Instruct-GGUF",
        "base": "deepseek",
        "cmd": [
            "base_cmd_0",
            "-c", "65536",
            "-b", "4096",
            "-ub", "1024",
            "--reasoning-budget", "1024",
            "--n-cpu-moe", "40",
            "--no-mmap",
        ],
        "role_score": {
            "agent": 2.0,
            "chatbot": 2.0
        },
        "notes": "Deepseek MoE. Have a try."
    },
]

def select_model(role: str, series: str = None):
    """
    role: 'agent' | 'chatbot'
    series: 'qwen3.5' | 'qwen3.6' | 'qwen3' | None
    
    Selection logic:
    1. If series is provided, search within that series; otherwise search all models
    2. Find the model with the highest score for the given role; if not found, default to agent score
    3. Print relevant information
    """
    # Determine candidate range: filter by series if provided, otherwise all
    candidates = MODEL_REGISTRY if not series else [
        m for m in MODEL_REGISTRY if m["base"] == series
    ]
    
    if not candidates:
        raise ValueError(f"No models found with base '{series}'")
    
    # Calculate each model's score for the current role
    def get_role_score(model):
        scores = model.get("role_score", {})
        # Use the provided role if available, otherwise default to 'agent'
        role_key = role if role in scores else "agent"
        return scores.get(role_key, 0.0), role_key
    
    # Find the model with the highest score
    best_model = max(candidates, key=lambda m: get_role_score(m)[0])
    best_score, effective_role = get_role_score(best_model)
    
    # Print relevant information
    print("=" * 60)
    print(f"[Model Selection Result]")
    print(f"  Requested Role: {role} | Series: {series or 'all'}")
    print(f"  Candidate count: {len(candidates)}")
    print(f"  Selected model: {best_model['name']}")
    print(f"  Repo: {best_model['repo']}")
    print(f"  Base series: {best_model['base']}")
    print(f"  Effective Role: {effective_role}")
    print(f"  Score: {best_score:.2f}")
    print(f"  Notes: {best_model.get('notes', 'N/A')}")
    print("=" * 60)
    
    return best_model['name'], best_model['repo']


###############################################################################


import os
import subprocess
import sys
import logging
import zipfile
import urllib.request

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("NativeEngine")

# Use the latest official verified release (as of 2026-04-25)
ORG = "ggml-org"
LLAMA_BUILD_ID = "b8925"
EXE_NAME = "llama-server.exe" # Latest version unified as llama-server.exe

BIN_DIR = os.path.join(BASE_DIR, "bin")
EXE_PATH = os.path.join(BIN_DIR, EXE_NAME)

# Named base_cmds, referenced by name
base_cmd_0 = [
    "-ngl", "all",
    "--host", "0.0.0.0",
    "--port", "11434",
    # "-t", "2", # Number of CPU threads
    # "-np", "1", # Number of concurrent requests
    # "-c", "131072", # Maximum context window size (tokens)
    "-ctk", "q8_0", # KV cache quantization for Keys
    "-ctv", "turbo4", # KV cache quantization for Values
    # "-b", "4096", # Logical batch size during prompt processing
    # "-ub", "1024", # Physical micro-batch size
    "-fa", "on", # Enable Flash Attention
    "--jinja", # Enable tokenizer chat template (Qwen models)
    # "--reasoning-budget", "1024", # Reasoning budget
    # "--n-cpu-moe", "32", # Number of MoE experts computed on CPU (A3B models)
    # "--no-mmap", # Avoid high GPU-Copy in cpu-moe
]
base_cmd_1 = [
    "-ngl", "all",
    "--host", "0.0.0.0",
    "--port", "11434",
    "-np", "1",
    "-c", "131072",
    "-ctk", "q8_0",
    "-ctv", "turbo4",
    "-b", "4096",
    "-ub", "1024",
    "-fa", "on",
    "--jinja",
    "--reasoning-budget", "1024",
    "--n-cpu-moe", "34",
    "--no-mmap",
]

base_cmds = {
    "base_cmd_0": base_cmd_0,
    "base_cmd_1": base_cmd_1,
}

def download_and_extract(url, target_dir):
    zip_path = os.path.join(target_dir, "temp.zip")
    try:
        logger.info(f"[INFO] Downloading: {url}")
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        os.remove(zip_path)
        return True
    except Exception as e:
        logger.error(f"[ERROR] Download/extract failed: {e}")
        return False

def ensure_binaries_exist():
    if os.path.exists(EXE_PATH):
        return True

    logger.info(f"[INFO] Downloading native CUDA 12.4 engine from {ORG}...")
    os.makedirs(BIN_DIR, exist_ok=True)
    
    # Core package (includes llama-server.exe)
    main_url = f"https://github.com/{ORG}/llama.cpp/releases/download/{LLAMA_BUILD_ID}/llama-{LLAMA_BUILD_ID}-bin-win-cuda-12.4-x64.zip"
    # Component package (includes necessary CUDA runtime DLLs)
    deps_url = f"https://github.com/{ORG}/llama.cpp/releases/download/{LLAMA_BUILD_ID}/cudart-llama-bin-win-cuda-12.4-x64.zip"

    # turboquant version
    # https://github.com/TheTom/llama-cpp-turboquant/releases/tag/tqp-v0.1.1

    if download_and_extract(main_url, BIN_DIR) and download_and_extract(deps_url, BIN_DIR):
        logger.info("[INFO] Native engine and CUDA components ready!")
        return True
    return False

def ensure_model_exists(model_name, model_repo):
    model_path = os.path.join(MODEL_DIR, model_name + ".gguf")
    print(f"{model_path}")
    if os.path.exists(model_path): return model_path
    try:
        from huggingface_hub import hf_hub_download
        logger.info(f"[INFO] Downloading from Hugging Face")
        hf_hub_download(
            repo_id=model_repo,
            filename=model_name,
            local_dir=os.path.dirname(model_path),
            local_dir_use_symlinks=False
        )
        return model_path
    except Exception as e:
        logger.error(f"[ERROR] Model download failed: {e}")
        return ""

def run_server():
    if not ensure_binaries_exist(): return
    
    model_name, model_repo = select_model("agent")
    model_path = ensure_model_exists(model_name, model_repo)
    if not model_path: return

    model_entry = next(m for m in MODEL_REGISTRY if m["name"] == model_name)
    model_cmd = model_entry.get("cmd", ["base_cmd_1"])

    logger.info("[INFO] [Native Engine] Starting...")

    final_cmd = [EXE_PATH, "-m", model_path]
    for part in model_cmd:
        if part in base_cmds:
            final_cmd.extend(list(base_cmds[part]))
        else:
            final_cmd.append(part)
    print(f"{final_cmd}")

    try:
        subprocess.run(final_cmd)
    except KeyboardInterrupt:
        logger.info("\n[INFO] Service stopped.")

if __name__ == "__main__":
    run_server()
