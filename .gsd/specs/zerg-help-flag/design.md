# Technical Design: mahabharatha-help-flag

## Metadata
- **Feature**: mahabharatha-help-flag
- **Status**: APPROVED
- **Created**: 2026-01-31
- **Author**: Factory Design Mode

---

## 1. Overview

### 1.1 Summary
Add `--help` flag to all 25 `/mahabharatha:` commands. When invoked with `--help`, Claude displays a formatted help block showing the command name, one-line description, and all available flags/options, then stops without executing the command. Implementation modifies existing command files only — no new files.

### 1.2 Goals
- Universal `--help` for every `/mahabharatha:*` command
- Consistent output format across all commands
- Zero new files — modify existing command markdown only

### 1.3 Non-Goals
- No runtime help system or Python module
- No interactive flag completion
- No man-page generation

---

## 2. Architecture

### 2.1 Modification Pattern

For each command file, add two things:

**1. Help flag in flags/usage section:**
```
- `--help`: Show command usage and available flags
```

**2. Help check at top of pre-flight (or add pre-flight if missing):**
```bash
# Help flag
if echo "$ARGUMENTS" | grep -q '\-\-help'; then
  cat << 'HELP'
/mahabharatha:{command} — {one-line description}

Flags:
  {flag1}    {description}
  {flag2}    {description}
  --help     Show this help message
HELP
  exit 0
fi
```

### 2.2 Two File Categories

| Category | Files | Modify |
|----------|-------|--------|
| Split commands (12) | debug, design, estimate, explain, init, merge, plan, plugins, kurukshetra, select-tool, status, worker | `.core.md` only (parent is copy of core) |
| Standalone commands (13) | analyze, build, cleanup, document, git, index, logs, refactor, retry, review, security, stop, test | `.md` (the only file) |

### 2.3 Post-Modification

After modifying `.core.md` files, regenerate parent `.md` files to match (copy core content, fix top split marker).

---

## 3. Key Decisions

### 3.1 Modify Core Only for Split Commands
**Context**: Split commands have core.md + parent.md with identical content.
**Decision**: Modify core.md, then copy to parent.md with adjusted split marker.
**Rationale**: Single source of truth. Parent = core content.

### 3.2 Inline Help Text
**Context**: Could use external help file or inline the help text.
**Decision**: Inline help text in pre-flight bash block.
**Rationale**: Self-contained, no file lookups, works everywhere.

---

## 4. Implementation Plan

### 4.1 Phase Summary

| Phase | Tasks | Parallel | Description |
|-------|-------|----------|-------------|
| Foundation (L1) | 5 | Yes | Add --help to all 25 commands (5 batches of 5) |
| Integration (L2) | 1 | No | Regenerate parent files for split commands |
| Quality (L3) | 1 | No | Verify all commands have --help, run tests |

### 4.2 Task Batches (L1)

| Batch | Commands |
|-------|----------|
| 1 | analyze, build, cleanup, debug, design |
| 2 | document, estimate, explain, git, index |
| 3 | init, logs, merge, plan, plugins |
| 4 | refactor, retry, review, kurukshetra, security |
| 5 | select-tool, status, stop, test, worker |

### 4.3 File Ownership

Each L1 task owns its batch of 5 command files (modify only).
L2 task owns all 12 parent .md files for split commands (modify only).

---

## 5. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Inconsistent help format | Low | Low | Template-based, workers follow same pattern |
| Parent files out of sync | Medium | Low | L2 task explicitly regenerates all parents |

---

## 6. Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Architecture | Factory Design | 2026-01-31 | APPROVED |
