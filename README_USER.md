# AgentOS 终端使用指南 (User Guide)

欢迎来到 **AgentOS** —— 一个专为 AI 智能体设计的“沙盒操作系统”。在这里，LLM 是 CPU，而你是指挥官。

---

## 🚀 启动 OS
在终端中执行以下命令进入 AgentOS 的根 Shell：
```powershell
python rootfs/busyagent.py
```
你将看到标志性的提示符：`AgentOS rootfs> `。

---

## 🛠️ 内置系统指令 (Applets)

系统内置了一系列工具（Applets），输入 `help` 可以随时查看：

### 1. `ls` - 查看已装载应用
查看内核当前注册的所有 AI 应用及其逻辑名称、版本和描述。
```bash
AgentOS rootfs> ls
```

### 2. `run <app_name>` - 前台运行应用
将指定应用调入前台执行。
- **示例**：`run chatbot`
- **注意**：此处需输入 Manifest 中定义的 `name`（逻辑名称）。可以使用 `exit` 随时退出应用返回 OS。

### 3. `gateway [start|stop]` - 启动/关闭万能网关
AgentOS 会在本地端口 `:8001` 启动一个伪装成 OpenAI 标准接口的拦截网关。
- **作用**：让你的其他 AI 测试程序通过 AgentOS 统一调度。
- **示例**：`gateway start`

### 4. `stats` - 实时遥测审计
查看当前系统所有算力流的统计信息（调用次数、Token 损耗、成功率、延迟等）。
```bash
AgentOS rootfs> stats
```

---

## 🧠 万能代理 (Universal AI Proxy Hub)

AgentOS 的核心功能之一是作为协议拦截器。

1. **配置**：让你的程序（如 Python 脚本、游戏引擎）指向 `http://localhost:8001/v1`。
2. **拦截模式**：
   - **隐式代理 (Implicit)**：模型名保持不变，AgentOS 会根据默认策略（如 `intent-proxy`）进行无感增强。
   - **显式劫持 (Explicit)**：将模型名设为 `app-name:model-name`。
     - **示例**：使用 `chatbot:gpt-4o` 作为模型名，请求将被强制重定向到 `chatbot` 应用执行。

---

## 📂 应用开发小知识

- **逻辑名 vs 物理名**：
  - 你可以把 App 放在 `apps/` 下的任何文件夹里。
  - 系统只认 `manifest.yaml` 里的 `name`。
- **配置文件**：
  - `config.py`：定义了系统允许调用的模型“白名单”和算力池。

---

## ⚠️ 注意事项
- **单向盲从**：当你感觉系统无法加载某个应用时，请检查 `ls` 列表，确保逻辑名称拼写正确。
- **计费安全**：所有非法调用（不在白名单内）的模型请求都会被内核调度器拦截，请放心调试。

---
*AgentOS: Rethink what an OS can be.*
