# AgentOS Harness: The AI Operating System

AgentOS 是一个生产级的 **Agent Harness**（智能体操作系统）。它将 LLM 作为 CPU 进行驱动，通过一套完整的基础设施实现可靠的自治 Agent 行为。

---

## 🗺️ 知识地图 (The Knowledge Portal)

作为开发者，请根据当前需求，按需加载以下认知模块：

### 1. 系统基因 (DNA)
- **[Philosophy](docs/philosophy.md)**: 为什么它是 OS？冯·诺依曼架构类比。
- **[Anatomy](docs/anatomy.md)**: Harness 的物理分层、内核态与用户态解剖。

### 2. 执行标准 (Engineering)
- **[Standards](docs/standards.md)**: 工程原则、计费红线、物理环境限制。
- **[Governance](docs/governance.md)**: 合规审计标准、作弊定义。
- **[Testing](docs/testing.md)**: 自动化测试体系与集成验证指南。

### 3. 系统指令库 (Instructions)
- 位于 `apps/*/prompts/` 目录。每个 App 都有自己彻底隔离的认知/指令体系（完全自治）。

---

## ⚡ 运行状态 (The Heartbeat)

- **[Roadmap](ROADMAP.md)**: 我们长期的目标与进化路径。
- **[Current Task](task.md)**: 我们现在正在做什么？
- **[Execution Plan](implementation_plan.md)**: 下一步计划怎么做？
- **[Walkthrough](walkthrough.md)**: 我们最近完成了什么？

---

## 🚀 开发者快速进场
1. 阅读根目录的 **[AGENTS_WORK_CODE.md](AGENTS_WORK_CODE.md)**（强制红线）。
2. 查看 **[README_INTERNAL.md](README_INTERNAL.md)**（即本文档）确定任务边界。
3. 进入 **[task.md](task.md)** 开始执行。

---
*If you are the model, remember: You are the CPU, Harness is your OS.*
