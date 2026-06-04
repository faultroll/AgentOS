# .a Architecture Decisions

> This document records significant architectural decisions for the project.

## Decision Record Template

```markdown
## ADR-XXX: [Title]

**Date**: YYYY-MM-DD
**Status**: Proposed / Accepted / Deprecated

**Context**:
[What is the issue?]

**Decision**:
[What is the change?]

**Consequences**:
- Positive: [benefits]
- Negative: [drawbacks]
```

---

## Active Decisions

### ADR-001: Plugin-Based Sandbox Over Container

**Date**: 2026-05-24
**Status**: Accepted

**Context**:
We need security isolation for AI coding agents without requiring Docker/Python dependencies.

**Decision**:
Use OS-level sandbox (Trae/VSCode style) as primary isolation mechanism.
- macOS: sandbox-exec
- Windows: Windows native / WSL2
- Linux: bubblewrap

**Consequences**:
- Positive: Zero dependency, Windows native support
- Negative: Less isolation than containers

---

### ADR-002: YAML/JSON for All Configuration

**Date**: 2026-05-24
**Status**: Accepted

**Context**:
Need human-readable, tool-parseable configuration format.

**Decision**:
All configuration in YAML or JSON. No binary formats.

---

### ADR-003: Markdown for Artifacts

**Date**: 2026-05-24
**Status**: Accepted

**Context**:
Need a format for Plan/Result/Review artifacts that is both human-readable and machine-parseable.

**Decision**:
Use Markdown with structured headers (Analysis, Tasks, Changes, etc.)

---

### ADR-004: Provider Abstraction via Continue

**Date**: 2026-05-24
**Status**: Accepted

**Context**:
Need flexibility to switch LLM providers without changing workflow.

**Decision**:
Use Continue as primary provider layer with YAML configuration.

---

### ADR-005: Multi-Agent via Kilo Code

**Date**: 2026-05-24
**Status**: Accepted

**Context**:
Need Planner/Worker/Reviewer orchestration.

**Decision**:
Use Kilo Code with custom prompts from `.a/prompts/`.
