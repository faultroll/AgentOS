# AgentOS 测试架构与规范 (Testing Guide v3)

为了匹配 v3 的 **Bootstrap 架构**与 **App 绝对隔离**设计，测试代码库也遵循**“职责分离、作用域物理隔离”**的铁律。

---

## 🏗️ 测试物理分层架构

### 层级 1: 内核与系统测试 (`/tests/`)
这里是 AgentOS 核心系统测试场。**严禁**在这里写入任何涉及具体 App 业务逻辑的代码，它只测试 OS 返回的系统级原语特性。

- **`/tests/test_kernel/` (内核基石测试)**:
  - 验证 `ProcessState` (PCB) 生命周期与载体隔离。
  - 验证 `ProcessTable` 对于 `manifest.yaml` 的强校验加载。
  - 验证 `ComputeScheduler` 根据遥测信息动态阻断并降级异常算力的核心规则。
  - 验证 `TelemetryBus` 日志池的读写机制。

- **`/tests/test_shell/` (网关与入口测试)**:
  - 跑通对 `api.py` 和 `cli.py` 这类 Bootstrap 接口的冒烟测试，确保从 HTTP 收到的参数正确压入 `ProcessState`。

### 层级 2: App 自治测试 (`/apps/*/tests/`)
按照微内核体系架构理念，应用是彻底解耦自治的模块。因此，应用程序的具体节点单元测试与其 LangGraph 连接管道自动化测试**必须紧邻它的存放位置**。

例如：`/apps/intent_proxy/tests/`
- `test_nodes.py`: 测试 Architecture 和 Auditing 节点的独立纯函数功能或 MCP IO。
- `test_integration.py`: 拼装当前 App 的 LangGraph 拓扑，喂入模拟对话流，测试终态的 `<blueprint>` 与 `<thought>`。

---

## ⚙️ 规范与运行哲学 

> [!CAUTION]
> **红线要求**：在执行 `python -m unittest` 时，OS 测试层不能引入任何未被隔离在 `/apps/` 目录下的系统内代码；而 App 测试层的引用必须局限在当前 App 的域与内核暴露接口之内。

### 运行方式 (Portable 兼容风格)
我们依赖内置的 `unittest` 从而保证能在无需任何外置 pip 工具的 Portable Conda 环境下健壮存活。

**运行全量 OS 级测试**:
在项目根目录执行：
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

**运行特定 App 的自动化验证**:
在项目根目录执行：
```powershell
python -m unittest discover -s apps/intent_proxy/tests -p "test_*.py"
```

## ⚖️ 编写测试的信条
- **可读性即文档**：测试代码不仅是校验逻辑，更是未来的 AI Staff 理解系统的**第一入口**。
- **强制 AAA 模式**：
  - `Arrange`: 明确构建物理场景（Mock 数据/环境变量）。
  - `Act`: 执行最小单元动作。
  - `Assert`: 进行多维度断言。
- **语义化日志演习**：测试中必须使用 `logger.info` 描述当前模拟的演习场景，模拟内核“黑盒”运行的直观反馈。
- **无状态验证**：只要不是测试 Memory，都应该使用 `unittest.mock` 去隔离网络，而不是真实挂载。
- **环境一致性保护**：绝不在 `test` 系代码层内部手动操作修改根节点任何 `sys.path`。

---

## 💎 内核加固测试哲学 (Hardened Testing Philosophy)

为了防止测试流于表面（Mock 滥用），AgentOS 强制执行以下加固标准：

### 1. 拒绝“一刀切”式 Patch
❌ **禁止**：使用 `unittest.mock.patch` 直接屏蔽底层库（如 `httpx`）。这种做法会跳过内核的 `Provider` 封装与 `Router` 循环逻辑。
✅ **提倡**：使用 **面向对象的子类 Mock (`FakeProvider`)**。通过继承 `BaseProvider` 并劫持 `PROVIDER_INSTANCES`，确保 100% 的内核逻辑（包括数据构造、循环 Fallback、异常转换）都得到真实执行。

### 2. “别名劫持”集成验证法 (Alias Hijacking)
在进行 `Harness` 全链路测试时，应保留 `config.py` 中的真实模型元数据（如 `context_window`），但人为将这些别名指向测试用的 `FakeProvider`。
- **目的**：验证调度器的**物理感知能力**（例如：任务太大会自动选择规格更高的别名核心）。
- **效果**：既保证了测试的逻辑真实性，又实现了 0 成本、毫秒级响应。

### 3. 遥测断言 (Telemetry Assertions)
测试不仅要验证函数的返回值，**必须断言全局副作用**。每一个 `call_llm` 测试都应检查 `TelemetryBus` 是否正确记录了对应的成功或失败事件。没有遥测断言的内核测试是不完整的。

---

## 🏛️ 上层建筑测试哲学 (Upper-Layer Testing Philosophy)

对于 Rootfs 或系统 App 层的测试，AgentOS 遵循**“下层透明、上层集成”**的准则：

### 1. 拒绝“假内核” (No Fake Kernel)
❌ **禁止**：在测试 Rootfs（如 Gateway, Applets）时 Mock 掉内核原语（如 `call_llm`, `Scheduler`）。这会导致测试完全脱离物理现实。
✅ **提倡**：**直接使用已加固的内核组件**。Rootfs 测试应该直接调用真实的内核函数，让数据流真实地穿过调度器与路由器。

### 2. “套娃式”劫持 (Layer-on-Layer Integration)
上层测试应复用下层测试的辅助工具。
- **实践**：Rootfs 层的全链路测试应直接引用 `tests.test_kernel.helpers.FakeProvider` 来作为物理终点。
- **价值**：如果内核升级了协议，Rootfs 的测试会由于由于底层链路断开而立即报错，从而实现**强耦合校验**，防止出现“底层改了，上层测试依然由于 Mock 而虚假通过”的情况。

### 3. 物理副作用校验 (Physical Effect Verification)
对于 App 和 Tool 的测试，禁止断言“方法已调用”，必须验证其产生的**物理副作用**。
- **实践**：在测试 Memory 工具时，必须检查对应的 `TEST_MEMORY_DIR` 下是否真的生成了磁盘文件；在测试 App 时，必须检查 `TelemetryBus` 是否记录了对应的执行指标。
- **意义**：这能发现 MCP 路径重定向失败或单例配置锁死导致的物理层 Bug。

### 4. 环境单例归位 (Singleton Stewardship)
由于 AgentOS 在统一进程内运行，上层测试必须负责清理全局单例（如 `global_telemetry` 和 `config.MEMORY_DIR`）。
- **要求**：在 `setUp` 中重置遥测总线并显式注入 `builtins._os_scheduler`，并在 `tearDown` 中销毁临时物理目录，确保每一个测试场景看到的系统状态都是纯净且可追溯的。

---

> [!NOTE]
> **Hardened Milestone (2026.04.26)**:
> 此次更新标志着 AgentOS 彻底清除了早期开发阶段残留的“虚假 Mock”风格。
> 我们通过物理拦截技术（FakeProvider & Singleton Stewardship）修复了内核单例路径锁定的架构偏误。
> **谨记：在 AgentOS 的物理世界中，没有任何 Patch 能胜过最真实的 I/O 断言。**

