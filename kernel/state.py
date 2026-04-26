"""AgentOS Kernel — Process State (Minimal PCB)

The Process Control Block (PCB) is the ONLY state carrier the kernel recognizes.
Strictly decoupled from application frameworks like LangGraph.
"""
from typing import TypedDict, Optional, Any
import uuid

class ProcessState(TypedDict):
    """
    AgentOS PCB — 纯净的物理契约
    内核不处理合并逻辑，只负责按地址/键值进行状态托管。
    """
    pid: str         # 进程唯一标识
    messages: list   # 原始消息流 (NL Bus)
    token_usage: int # 资源消耗审计
    is_finished: bool# 生命周期标志
    os_signal: Optional[str] # 内核中断信号 (如 CONTEXT_PRESSURE)
    is_error: bool   # 异常标志
    app_state: dict  # 应用私有内存 (内核透明)

def create_process(query: str, app_name: str = "default") -> ProcessState:
    """物理初始化一个 PCB 实例"""
    return {
        "pid": f"{app_name}-{uuid.uuid4().hex[:8]}",
        "messages": [{"role": "user", "content": query}],
        "token_usage": 0,
        "is_finished": False,
        "os_signal": None,
        "is_error": False,
        "app_state": {},
    }
