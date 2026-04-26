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
- **无状态验证**：只要不是测试 Memory，都应该使用 `unittest.mock` 去隔离网络，而不是真实挂载。
- **环境一致性保护**：绝不在 `test` 系代码层内部手动操作修改根节点的任何 `sys.path`，请依托命令行的执行层环境推断能力。
