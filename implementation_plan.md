# AgentOS Phase 7: Memory Convection & Governance Decoupling

## 核心进展

### 1. 治理逻辑下沉 (Phase 7.5) - [DONE]
我们已成功将“上下文压缩与语义打捞”算法从 `apps/` 目录剥离。
*   **新组件**：`tools.memory.govern_context` 工具。
*   **技术契约**：工具层封装了 `Threshold Check`、`L2 Summarization`、`Semantic Salvage (1+1+1+2)` 三项核心能力。
*   **收益**：
    *   **彻底解耦**：App 节点（Audit）现在仅作为一个简单的 MCP 代理。
    *   **逻辑集中**：所有的内存回收策略统一在 Rootfs 侧维护。

### 2. 内核加固 (Phase 7.1) - [DONE]
*   **物理信号**：`os_signal` 正式列入 PCB 字段。
*   **精确覆盖**：PCB 状态更新由应用层手动缝合，内核仅提供物理承载。

## 后续路径 (Next)
- **Phase 9**: 虚拟化上下文中间件。
- **IPC 激活**：多进程下的信号同步。
