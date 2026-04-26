# AgentOS 开发任务清单

## ✅ 已完成 (Done)
- [x] Phase 6.6: 盲目性原则贯彻 (完成架构解耦)
- [x] **Phase 7: 记忆系统强化 (Memory & Context Guard)**
    - [x] **Kernel 加固**: 完成全链路物理测试加固，修复 mcp_server 与调度器 import 隐患。
    - [x] **稳定保障**: Kernel/Rootfs/App 全场景真核测试通过，文档已沉淀。
    - [x] **ContextProtector & Tools**: `summarize_context` 工具通过物理验证。
    - [x] **App 联动**: 在 `IntentProxy` 中打通物理链路转发流程。
- [x] **Phase 7.5: 治理能力工具化 (Governance Migration)**
    - [x] **逻辑迁移**: 将上下文缝合与语义打捞算法搬迁至 `tools/memory.py`。
    - [x] **App 减负**: `IntentProxy` 已切换为纯净的代理模式。
    - [x] **测试归位**: 建立了纯净的 `test_governance_logic.py`，并将 App 测试移至其专属路径。

## 🟢 近期规划 (Next)
- [ ] **Phase 8: 稳定性与自审计**
    - [ ] **Evaluator App**: 对系统各链路进行非侵入式质量审计。
- [ ] **Phase 9: 虚拟化上下文 (Virtual Context Space)**
    - [ ] **透明治理**: 在内核中断流中实现自动治理。

## 待办列表 (Backlog)
- [ ] IPC 策略层激活 (Mailbox 异步协议)
- [ ] EvoMap (认知图谱升级)
