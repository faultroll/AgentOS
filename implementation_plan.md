# Phase 6.6: 盲目性原则贯彻与网关转发修复 (Rootfs/Kernel Hardening)

本次更新旨在彻底修正前一任开发者留下的架构违规，将网关（Gateway）与应用（Apps）解耦，落实 AgentOS 的“盲目性原则”。

## 核心设计修正

> [!IMPORTANT]
> **网关定性**：Gateway 是 Rootfs 下的一个标准 Applet，其职责仅限于“算力请求的拦截、伪装与分发”。
> **盲目性执行**：网关严禁通过 `importlib` 或文件系统直接调起 `apps/` 下的代码。它应当只与 Kernel（Router/Scheduler）对话。

## Proposed Changes

### [Component] Rootfs (Gateway Hub)
#### [MODIFY] [gateway.py](file:///e:/Codes/agent/agentos/rootfs/applets/gateway.py)
- **删除**：所有关于应用探测、模块加载（importlib）和应用实例化的逻辑。
- **重构**：将所有拦截到的请求直接通过 `kernel.compute.router.call_llm` 转发。
- **降级保护**：当目标应用（Telemetry 标签）不存在时，系统不再报错 404，而是将其视为一个普通的“原子算力请求”进行调度。

### [Component] Kernel (Compute)
#### [MODIFY] [router.py](file:///e:/Codes/agent/agentos/kernel/compute/router.py)
- 确保 `call_llm` 能够接受来自 Rootfs 的原始请求，并根据 `Scheduler` 的决策进行多模型回退。

### [Component] Rootfs (Process Table)
#### [MODIFY] [busyagent.py](file:///e:/Codes/agent/agentos/rootfs/busyagent.py)
- 仅保留 `ProcessTable` 的扫描功能，供 Shell 列表查看，严禁网关等基础组件依赖其内容进行执行逻辑决策。

## Verification Plan

1. **极端环境启动**：移除 `apps/` 目录，运行 `python rootfs/busyagent.py`，确保无报错。
2. **网关透明转发**：在无 App 注册的情况下，运行 `gateway start`，并使用测试程序请求 `:8001`，验证是否能输出结果。
3. **遥测审计**：使用 `stats` 命令检查是否记录了 `gw.bypass` 来源的流量。
