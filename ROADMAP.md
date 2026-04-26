# AgentOS 演进路线图 (Roadmap)

> [!NOTE]
> 本文档由 Architect (Human) 与 AI Staff 共同维护，用于指导 AgentOS 的开发重心。
> 它是系统从 "Bootstrap" 走向 "Self-Evolution" 的导航图。

---

## 🔵 历史里程碑 (Completed)
- **Phase 1-6**: 核心内核、Rootfs 结构、多 Provider 路由、基本 Telemetry 落地。
- **Phase 7**: **记忆金字塔落地**。实现了 L1 (工作记忆) -> L2 (情节摘要) -> L3 (持久事实) 的物理流转与落盘验证。

## 🟢 正在/计划运行 (Immediate Focus)
- **Phase 8: 系统自我审计与稳定性 (Stability First)**
    - **Evaluator App**：引入 "LLM-as-a-Judge"，对其他 App 的输出进行非侵入式质量审计。
    - **Coding App**：具备编写代码并进行单元测试的专项应用（Self-iteration 的前置）。
- **Phase 9: 虚拟化上下文空间 (Virtual Context Space)**
    *   **透明治理**：在 `kernel.call_llm` 中实现自动治理拦截器。当信号触发时，内核自动驱动 `govern_context` 工具。
    *   **MMU 模拟**：让应用层彻底告白对 Token 限制的焦虑，实现逻辑上的“无限上下文”。

## 🟡 近期规划 (Next Paths)
- **IPC 策略层激活**：在多 App 共存环境下，正式开启 Mailbox 的异步通信协议。
- **Tools 热加载 (Insmod)**：实现非自然语言代码工具的动态注册与卸载。

## 🟠 中长期愿景 (Vision)
- **EvoMap (认知图谱)**：将扁平的 Markdown 记忆升级为具备关联性的知识图谱，解决长程检索的衰减问题。
- **GAN / 反馈强化循环**：通过生成型对抗机制，实现 App 指令（Prompts）的自我进化。

## 🔴 终极目标 (The Singularity)
- **Self-iteration (自我迭代)**：实现 Coding App 修改 `kernel/` 源码并热重载，完成 OS 级的闭环演进。

---
*Last Updated per Phase 7.5 Governance Decoupling Completion.*
