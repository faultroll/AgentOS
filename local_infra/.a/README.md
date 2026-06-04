# .a AI Coding Workspace

A portable, reproducible AI coding runtime for VSCodium.

## Overview

The `.a` workspace provides:
- Planner/Worker/Reviewer multi-agent workflow
- Plugin-based sandbox isolation
- Provider abstraction for LLM backends
- Transparent configuration (YAML/JSON/Markdown)
- Zero-dependency portable setup

## Quick Start

### Prerequisites

1. PowerShell execution policy configured:
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. LLM backend (user-managed):
   - Ollama, OpenAI API, or any OpenAI-compatible endpoint

### Installation

```powershell
# Clone or download the workspace
git clone <repository-url>
cd <project-directory>

# Run installer
.a/install.ps1
```

### Launch Workspace

```powershell
.a/bootstrap.ps1
```

### Configure LLM Backend

Edit `.a/providers/continue.yaml` to set your LLM endpoint:

```yaml
models:
  - name: My LLM
    provider: ollama  # or openai
    model: qwen2.5-coder:7b
    apiBase: http://127.0.0.1:11434
```

## Directory Structure

```
.a/
├── prompts/           # Role prompts (Planner/Worker/Reviewer)
├── providers/         # LLM provider configurations
├── sandbox/           # Security sandbox policy
├── memory/            # Architecture decisions and conventions
├── vscode/            # IDE settings
├── install.ps1        # Installation script
├── bootstrap.ps1      # Launch script
├── requirements.txt   # Version dependencies
└── PLAN.md            # Detailed plan document
```

## Components

### Continue (Provider Layer)
- LLM abstraction layer
- Supports Ollama, OpenAI, OpenRouter, etc.
- Configured via `.a/providers/continue.yaml`

### Kilo Code (Orchestration Layer)
- Multi-agent collaboration
- Planner/Worker/Reviewer modes
- Worktree isolation support

### Sandbox (Security Layer)
- OS-level file system isolation
- Network access control
- Configured via `.a/sandbox/sandbox.json`

## Workflow

```
User Request → Planner → PLAN.md → Worker → RESULT.md → Reviewer → REVIEW.md
```

### Planner
- Decomposes tasks into actionable steps
- Maintains architecture memory
- Outputs structured PLAN.md artifacts

### Worker
- Executes tasks from PLAN.md
- Runs in sandboxed environment
- Produces RESULT.md artifacts

### Reviewer
- Validates code changes
- Checks style and conventions
- Provides PASS/FAIL verdict

## Security

- Plugin-based OS sandbox (no Docker required)
- File system whitelist
- Network access control
- All configurations are transparent

## Version Requirements

| Component | Version |
|-----------|---------|
| VSCodium | 1.95.0+ |
| Continue | 0.12.0+ |
| Kilo Code | 1.5.0+ |

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues or questions, please open an issue in the repository.
