# AgentOS 开发者守则 (Bootloader)

> [!CAUTION]
> **致所有开发者（AI 助手）**：在开始工作前，你必须全文阅读本守则。
> **认知边界警示**：当你编辑 `prompts/` 或 `memory/` 时，你是在编写“运行代码”，严禁泄露 `docs/` 下的物理实现细节（如代码路径）。
> **ERROR NO.1**: 在阅读 [README_INTERNAL.md](README_INTERNAL.md) 中的“知识地图”之前，严禁进行任何代码修改。

---

## 🛡️ 执行红线 (The Red Lines)

### 1. 物理安全 (Physical Safety)
- **零体力原则**：你具备脑力（设计/编码），但**零体力**（执行/安装）。
- **禁止行为**：❌ 运行 `python` 脚本、❌ `pip install`、❌ 启动服务器。
- **强制要求**：所有操作必须转化为 **Markdown 指令**交给人类用户执行。

### 2. 算力与计费 (Billing Safety)
- **白名单机制**：❌ 绝对禁止调用 `config.py` 之外的模型。
- **强制拦截**：所有请求必须通过 `kernel/compute/router.py`。

### 3. 系统主权 (Architectural Integrity)
- **Harness 中立性**：严禁为了修复业务 App 的 Bug 而修改 Harness 内核（`kernel/`）。
- **盲目性原则 (Ignorance Principle)**：遵循严格的层级解耦（Layered Agnosticism）。
  - **单向可见原则**：底层组件严禁感知上层组件的存在。每一层仅允许调用其内部资源或其物理下层组件提供的正式接口。
  - **白名单通信**：严禁跨层级直接触达、导入或根据上层逻辑进行分支判断。例如：内核严禁感知 Rootfs 的实现，Rootfs 严禁感知 Apps 的物理内容。
- **模块化优先**：禁止 Monolith Prompt。

### 4. 稳定性保障 (Stability Assurance)
- **内核加固原则**：鉴于 Kernel 已进入稳定期，❌ **绝对禁止**在没有配套测试的情况下修改内核。
- **强制要求**：所有对 `kernel/` 的逻辑改动，必须在 `tests/` 目录下配套新增/更新测试，并遵守以下 **[测试可读性规范]**：
  - **AAA 结构**：代码必须按 `Arrange` (准备), `Act` (执行), `Assert` (验证) 结构化编写。
  - **语义化日志**：必须在测试关键路径输出 `logger.info`，模拟“内核演习场景”。
  - **中英双语 Docstrings**：详述测试的物理背景与预期，确保未来的 AI Staff 能秒读业务含义。

---

## 🛰️ 快速引导 (Fast Onboarding)

1. **第一步**：阅读 [README_INTERNAL.md](README_INTERNAL.md) 获取系统全景索引。
2. **第二步**：阅读 [task.md](task.md) 了解当前任务进度。
3. **第三步**：根据任务需求，从 `docs/` 目录按需加载特定的认知模块（如 `docs/anatomy.md`）。

---
**声明**：违反守则（尤其是擅自尝试执行代码或导致计费泄露）将被视为严重失职。
