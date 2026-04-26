# Harness 核心架构解剖 (Anatomy)

本模块定义了 AgentOS v3 (Bootstrap 架构) 的物理层级与解剖学结构。

---

## 1. 五层物理实现 (Internal Layers)

### 1) Harness 内核态 (Kernel Space)
- **位置**：`/kernel`
- **定位**：纯代码，零自然语言。负责状态管理和算力/IO原语。
- **组件**：
    - `state.py` / `process.py`: Harness 的 PCB（进程控制块）和生命周期管理。
    - `memory.py` / `ipc.py`: 内存作用域隔离与进程间通信邮箱。
    - `compute/`: 算力调度中心 (`scheduler.py`) 与执行路由 (`router.py`)。
    - `telemetry.py`: 系统遥测总线（纯结构化数据反馈）。
    - `drivers/`: MCP 驱动层，负责底层通讯。

### 2) Harness 接口态 (Shell)
- **位置**：`/shell`
- **定位**：Bootstrap 初始化点与系统网关。
- **组件**：
    - `api.py`: 网络 Shell（HTTP OpenAI 接口）。
    - `cli.py`: 终端 Shell（本地交互）。

### 3) 业务态 (Apps)
- **位置**：`/apps`
- **定位**：每个 App 完全自治，拥有自己的 Manifest、Prompt 和 Memory。
- **结构**：
    - `manifest.yaml`: 向内核声明工具依赖和算力偏好。
    - `prompts/`: 隔离的运行时自然语言指令。
    - `memory/`: 进程级地址空间隔离的事实库。
    - `app.py`: 业务 LangGraph 拓扑。

### 4) 数据持久层 (Global Memory)
- **位置**：`/memory/global`
- **定位**：OS 级事实库（仅内核与可信 App 可写）。

### 5) 驱动池 (Tools Device Registry)
- **位置**：`/tools`
- **定位**：所有的 MCP Tool 工具池，App 按照 Manifest 取用对应的驱动。

## 2. 状态流转契约
Harness 内核只搬运 `ProcessState`。所有应用特有的上下文（如 `plan_intelligence`）都被封装在不透明的 `app_state` 对象中。内核不会尝试理解或修改这些数据。

## 3. 价值保障
- **环境隔离**：一个 App 里的系统提示词不可能泄露给另一个 App。
- **可观测反馈**：通过 `kernel/telemetry.py`，OS 实现了算力的闭环跟踪。
- **全自然语言闭环**：所有的模型逻辑都在 App 中通过 Prompt 动态构建。
