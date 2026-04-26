# AgentOS 架构演进路线 (Walkthrough)

## Phase 6: 治理、评估与 Busybox 系统级重构

**代号：军刀 (Saber)**

本次迭代极大深化了 OS 内核与 App 的边界，彻底完成了控制流倒置。

### 1. "Busybox" CLI 运行时重构
- 现在的 `shell/cli.py` 表现地像一个真正的 OS 终端 / Rootfs。
- **清除特例**：移除了代码中 `if app_name == "intent-proxy"` 这样的硬编码，取而代之的是动态 `importlib` 反射机制和签名侦测。只要将符合 `manifest.yaml` 声明与 `build_app()` 接口的包放入 `apps/` 目录下，CLI 就能在启动时即插即用地发现并加载它们。
- **瞬态系统监控**：在 CLI REPL 会话中内置了 `/stats` 指令，能够不落盘地直接透传输出位于内核级 `TelemetryBus` 提供的大模型运行时耗、Token 开销和吞吐健康度等关键指标，坚持了内核态保持纯净的原则。

### 2. API 网关泛型化 (Dynamic Router)
- 对 `shell/api.py` 的改造意味着它现在真正充当了 HTTP 请求的路由分配器。
- 支持类似于 `model="intent-proxy:qwen"` 或 `"chatbot:gpt-4"` 的前缀解析模式，API 接口可以无缝地将 OpenAI 标准请求投送到内存中唤醒的不同 App 虚拟进程中，实现了网络访问通道对所有 App 无差别赋能。

### 3. Evaluator 守护进程 (Service App)
- 新增 `apps/evaluator` 作为一个特殊的服务类 (Daemon) App：
  - 拥有自己的 `manifest.yaml`，不需要对外暴露任何 Tool 接口，只需要配置 `read_file` 的权限。
  - 它的角色是系统级的内省大内密探，在后台（独立调用模型与隔离记忆库）对系统的会话数据和 Telemetry 进行打分，完成了 LLM-as-Judge 的闭环，同时完全没有污染核心的执行流。

---

## Phase 5: v3 Big Bang 架构重构回顾

### 内核状态纯粹化 (Kernel State)
**Before**: `AgentState` 包含各类业务特定的字段从而形成巨石架构。
**After**: `ProcessState` 蜕变为纯血的进程控制块 (PCB)，业务状态下放为不透明的 `app_state` 对象。

### 算力分离与遥测 (Scheduler & Telemetry)
**Before**: `router.py` 硬编码耦合度高，没有 OS 级的遥测系统。
**After**: `telemetry.py` 和 `scheduler.py` 组合构成了监控收集和智能降级的完整计算平台。

### 应用级闭环自治 (App Autonomy)
**Before**: `prompts/` 作为全局目录指令化所有业务。
**After**: 系统实现物理级别的沙盒隔离（自身的指令库 `prompts/` 和数据堆 `memory/` 脱离 OS 的感知域成为 App 私有财产）。
