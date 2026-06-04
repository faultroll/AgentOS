# `.a` Build Plan

> **Status**: Draft v2.0
> **Date**: 2026-05-24
> **Target**: Build `.a` — A Reproducible Open Agent Runtime for VSCodium

---

## Executive Summary

Build a portable, reproducible, open-source AI coding runtime (`.a/`) that can be cloned into any software project. The system uses **plugin-based sandbox isolation** (no Docker/Python dependency), **provider abstraction**, and **artifact-driven workflows**.

**Design Philosophy**:
- `.a` 定义**契约**（配置 + 提示词），不定义**实现**（执行逻辑）
- 插件可替换，架构掌握在 `.a` 手中
- 全透明，无隐藏逻辑

**用户操作流程**:
```
1. 安装 VSCodium
2. 安装 Continue + Kilo Code 插件
3. 把 .a 目录拷贝/链接到目标工程
4. 在插件里加载 .a/prompts/*.md 作为系统提示词
5. 开始对话 → 插件自动处理 Planner/Worker/Reviewer
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         .a/                                 │
│         (配置文件 + 提示词模板 + 安全策略)                    │
│                                                             │
│   定义 WHAT (做什么)，不定义 HOW (怎么做)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │ YAML/JSON/Markdown 契约
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Plugin Layer                              │
│                                                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │  Provider   │  │  Sandbox    │  │   Multi-    │        │
│   │  (Continue) │  │  (Built-in) │  │   Agent     │        │
│   │             │  │             │  │  (Kilo)     │        │
│   └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Directory Structure

```
.a/
├── prompts/           # 角色提示词 (核心资产)
│   ├── planner.md        # Planner 系统提示词
│   ├── worker.md         # Worker 系统提示词
│   └── reviewer.md       # Reviewer 系统提示词
│
├── providers/        # 模型配置 (可替换插件)
│   ├── continue.yaml     # Continue 配置 (Provider)
│   └── kilo.yaml         # Kilo Code 配置 (Orchestration)
│
├── sandbox/          # 安全策略 (可替换插件)
│   └── sandbox.json      # Trae/VSCode 风格白名单
│
├── memory/           # 持久化上下文 (人类维护)
│   ├── architecture.md    # 系统架构决策
│   └── conventions.md    # 代码规范
│
└── vscode/           # IDE 设置 (可选)
    └── settings.json     # VSCodium 配置
```

**已删除** (插件自带，无需 .a 提供):
- ❌ `hooks/` - 插件有内置 hook 机制
- ❌ `orchestration/*.yaml` - 插件自带编排
- ❌ `tasks/` / `results/` - 插件自己管理
- ❌ `docker/` - 插件沙箱覆盖

---

## Technology Stack

### Provider Layer — Continue

| 项目 | 说明 |
|------|------|
| **作用** | LLM 调用抽象、提示词透明化 |
| **优势** | MIT 协议、YAML 配置、1M+ 下载量、支持 Ollama/OpenAI/OpenRouter |
| **配置方式** | `providers/continue.yaml` |

### Orchestration Layer — Kilo Code

| 项目 | 说明 |
|------|------|
| **作用** | 多 Agent 协作、Planner/Worker/Reviewer 模式 |
| **优势** | 3M+ 下载、OpenCode (MIT)、500+ 模型、并行 subagent |
| **配置方式** | `providers/kilo.yaml` + `prompts/*.md` |

### Sandbox Layer — Built-in (Trae/VSCode Style)

| 项目 | 说明 |
|------|------|
| **作用** | OS 级安全隔离、文件系统白名单 |
| **优势** | 无需 Docker、原生支持 Windows/macOS/Linux |
| **配置方式** | `sandbox/sandbox.json` |

---

## Recommended Models

| Model | Use Case | VRAM | Source |
|-------|----------|------|--------|
| Qwen2.5-Coder 7B | General coding | 4.5GB | Ollama |
| Qwen2.5-Coder 1.5B | Fast autocomplete | 1GB | Ollama |
| DeepSeek-Coder 6.7B | Alternative | 4GB | Ollama |

---

## Sandbox Security Policy

` sandbox/sandbox.json`:

```json
{
  "filesystem": {
    "readWrite": ["$WORKSPACE_FOLDER"],
    "readOnly": ["/", "$HOME/.cache", "$HOME/.local/lib"]
  },
  "network": {
    "default": "deny",
    "allow": []
  }
}
```

**Platform Support**:

| Platform | Mechanism |
|----------|-----------|
| macOS | `sandbox-exec` |
| Windows | Windows native (WSL2 supported) |
| Linux | `bubblewrap` |

---

## Role Prompts (Core Assets)

### Planner

- **职责**: 分解任务、生成计划、维护架构记忆
- **禁止**: 直接编辑代码、执行 shell 命令
- **输出**: Markdown 格式的 Plan artifact

### Worker

- **职责**: 读取 Plan、执行任务、生成 Result
- **特性**: 无状态 (插件管理上下文)
- **输出**: Markdown 格式的 Result artifact

### Reviewer

- **职责**: 验证 diff、检测回归、确保规范
- **输出**: PASS / FAIL / REVISION_REQUIRED

---

## Execution Phases

### Phase 1: Foundation (Week 1)

| Step | Task | Deliverable |
|------|------|-------------|
| 1.1 | Create `.a/` directory structure | Complete scaffold |
| 1.2 | Write `prompts/planner.md` | Planner prompt |
| 1.3 | Write `prompts/worker.md` | Worker prompt |
| 1.4 | Write `prompts/reviewer.md` | Reviewer prompt |
| 1.5 | Create `providers/continue.yaml` | Continue config |
| 1.6 | Create `providers/kilo.yaml` | Kilo config |
| 1.7 | Create `sandbox/sandbox.json` | Security policy |
| 1.8 | Create `memory/architecture.md` | Architecture doc |
| 1.9 | Create `memory/conventions.md` | Code conventions |
| 1.10 | Create `vscode/settings.json` | IDE settings |

**Success Criteria**: `.a` 目录完整，配置可被插件加载。

### Phase 2: Integration (Week 2)

| Step | Task | Deliverable |
|------|------|-------------|
| 2.1 | Install VSCodium + plugins | Dev environment ready |
| 2.2 | Configure Continue with Ollama | Local LLM working |
| 2.3 | Configure Kilo Code | Agent modes functional |
| 2.4 | Test sandbox isolation | Security policy enforced |
| 2.5 | Load `.a/prompts/*.md` | Prompts loaded in plugins |
| 2.6 | End-to-end task test | Single-file edit via Planner/Worker/Reviewer |

**Success Criteria**: 完整任务通过 Planner → Worker → Reviewer 流程完成。

### Phase 3: Multi-File & Reproducibility (Week 3)

| Step | Task | Deliverable |
|------|------|-------------|
| 3.1 | Test multi-file feature | Cross-file refactor |
| 3.2 | Test git worktree isolation | Kilo Agent Manager |
| 3.3 | Create bootstrap guide | README.md |
| 3.4 | Document plugin swap | How-to replace Provider |

**Success Criteria**: 用户可按文档完成"clone + 安装插件 + 对话"全流程。

---

## Artifact Contracts

### PLAN.md (Planner 输出)

```markdown
# Plan: [Task Name]

## Analysis
[Why this task is needed]

## Tasks
1. [Subtask] → [File(s)]
2. ...

## Constraints
- [Non-negotiable requirements]

## Walkthrough
[Step-by-step for Worker]
```

### RESULT.md (Worker 输出)

```markdown
# Result: [Task Name]

## Completed
- [What was done]

## Changes
[File diffs]

## Notes
[Issues or observations]
```

### REVIEW.md (Reviewer 输出)

```markdown
# Review: [Task Name]

## Status
PASS / FAIL / REVISION_REQUIRED

## Issues
- [Problems]

## Suggestions
- [Improvements]
```

---

## Critical Design Rules

1. **契约驱动** — `.a` 定义 WHAT，插件定义 HOW
2. **插件可替换** — 换插件 = 换配置，不改 `.a` 核心
3. **全透明** — 所有配置可见可审计
4. **零依赖** — 不需要 Docker/Python/额外运行时
5. **即插即用** — `git clone` + 安装插件 = 即可用

---

## Plugin Swap Guide

| 替换目标 | 操作 |
|---------|------|
| **Provider** | 修改 `providers/continue.yaml` |
| **Orchestration** | 修改 `providers/kilo.yaml` + `prompts/*.md` |
| **Sandbox** | 修改 `sandbox/sandbox.json` (如果新插件支持) |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-24 | Initial plan with hooks/orchestration |
| 2.0 | 2026-05-24 | Simplified: removed hooks/orchestration/scripts |
