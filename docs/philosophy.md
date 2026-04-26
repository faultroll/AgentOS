# Harness 哲学与冯·诺依曼架构 (Philosophy)

这是 AgentOS 的“灵魂”模块。它解释了 Harness 各种技术选型背后的核心思考。

---

## 1. Harness 哲学 (The Harness Metaphor)
- **Harness = Operating System**：我们要构建的不是 Prompt 包装盒，而是智能体的操作系统。
- **解耦逻辑**：
    - **CPU (Computing)**: LLM 无状态推理引擎。
    - **RAM (Context)**: 上下文窗口（由 `kernel/state.py` 管理）。
    - **Disk (Storage)**: 长期记忆与状态持久化（由 `memory/` 模块负责）。
    - **Drivers (I/O)**: MCP 工具集与 I/O 驱动。
- **Agent 本质**：Agent 的行为是这套 Harness 驱动模型产生的涌现行为。

## 2. Harness 工程优先
行业经验（如 Anthropic Claude Code）证明：优化 Harness 的架构（编排、记忆管控、物理隔离）带来的性能提升提升，远超单纯的 Prompt 调优。

## 3. Role A/B 架构逻辑
- **Role A (Intent Architect)**：Harness 的策略编译态。负责背景理解、策略制定。
- **Role B (Worker)**：Harness 的执行交付态。负责工具调用、任务闭环。

## 4. 分层意图解析
为了平衡交互频率与成本，Harness 采用三级过滤：
1. **Heuristic (代码层)**：关键词匹配、状态机。
2. **Nano LLM (本地层)**：极速分类模型（llama.cpp）。
3. **Strategic LLM (云端层)**：全能型云端免费模型。

## 5. 基础设施独立性
- **Sibling Module 模式**：本地推理引擎（`local_infra`）作为 Harness 的兄弟模块，通过 OpenAI API 协议标准通讯，不共享内存或底层变量。
