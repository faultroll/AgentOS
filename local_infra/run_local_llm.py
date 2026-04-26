import os
import subprocess
import sys
import logging
import zipfile
import urllib.request

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("NativeEngine")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(BASE_DIR, "bin")

# 采用官方最新验证的 Release (截至 2026-04-25)
ORG = "ggml-org"
LLAMA_BUILD_ID = "b8925"
EXE_NAME = "llama-server.exe" # 最新版已统一命名为 llama-server.exe
EXE_PATH = os.path.join(BIN_DIR, EXE_NAME)

def download_and_extract(url, target_dir):
    zip_path = os.path.join(target_dir, "temp.zip")
    try:
        logger.info(f"⏳ 正在下载: {url}")
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        os.remove(zip_path)
        return True
    except Exception as e:
        logger.error(f"❌ 下载/解压失败: {e}")
        return False

def ensure_binaries_exist():
    if os.path.exists(EXE_PATH):
        return True

    logger.info(f"🕵️ 正在从 {ORG} 下载原生 CUDA 12.4 引擎...")
    os.makedirs(BIN_DIR, exist_ok=True)
    
    # 核心包 (包含 llama-server.exe)
    main_url = f"https://github.com/{ORG}/llama.cpp/releases/download/{LLAMA_BUILD_ID}/llama-{LLAMA_BUILD_ID}-bin-win-cuda-12.4-x64.zip"
    # 组件包 (包含必要的 CUDA 运行时 DLL)
    deps_url = f"https://github.com/{ORG}/llama.cpp/releases/download/{LLAMA_BUILD_ID}/cudart-llama-bin-win-cuda-12.4-x64.zip"

    if download_and_extract(main_url, BIN_DIR) and download_and_extract(deps_url, BIN_DIR):
        logger.info("✅ 原生引擎及 CUDA 组件准备就绪！")
        return True
    return False

def ensure_model_exists(model_path):
    if os.path.exists(model_path): return True
    try:
        from huggingface_hub import hf_hub_download
        logger.info(f"⏳ 正在从 Hugging Face 下载 Qwen 2.5...")
        hf_hub_download(
            repo_id="bartowski/Qwen2.5-7B-Instruct-GGUF",
            filename="Qwen2.5-7B-Instruct-Q5_K_M.gguf",
            local_dir=os.path.dirname(model_path),
            local_dir_use_symlinks=False
        )
        return True
    except Exception as e:
        logger.error(f"❌ 模型下载失败: {e}")
        return False

def run_server():
    if not ensure_binaries_exist(): return
    
    MODEL_PATH = os.path.join(BASE_DIR, "models", "Qwen2.5-7B-Instruct-Q5_K_M.gguf")
    if not ensure_model_exists(MODEL_PATH): return

    PORT = 11434
    GPU_LAYERS = 35 

    logger.info("🚀 [Native Engine] 启动中...")
    cmd = [
        EXE_PATH,
        "-m", MODEL_PATH,
        "-ngl", str(GPU_LAYERS),
        "--port", str(PORT),
        "--host", "0.0.0.0",
        "-c", "8192"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        logger.info("\n🛑 服务停止。")

if __name__ == "__main__":
    run_server()
