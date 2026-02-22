# /mahabharatha:cleanup

Remove MAHABHARATHA artifacts and clean up resources after a feature is complete or abandoned.

## Synopsis

```
/mahabharatha:cleanup [OPTIONS]
```

## Description

`/mahabharatha:cleanup` removes temporary resources created during MAHABHARATHA execution, including git worktrees, worker branches, Docker containers, state files, and log files. It preserves spec files, design documents, merged code, and task archives.

Before removing any state, the command archives the Claude Code Task list to `.mahabharatha/archive/<feature>/tasks-<timestamp>.json`.

### What Gets Removed

| Resource | Path / Pattern | Removed |
|----------|----------------|---------|
| Git worktrees | `.mahabharatha/worktrees/<feature>-worker-*` | Yes |
| State files | `.mahabharatha/state/<feature>.json` | Yes |
| Log files | `.mahabharatha/logs/worker-*.log` | Unless `--keep-logs` |
| Git branches | `mahabharatha/<feature>/*` | Unless `--keep-branches` |
| Docker containers | `mahabharatha-worker-<feature>-*` | Yes |

### What Is Preserved

- Source code and commits on the main branch
- Merged changes already in the target branch
- Spec files in `.gsd/specs/<feature>/` (requirements, design, task graph)
- Task archive in `.mahabharatha/archive/<feature>/`

## Options

| Option | Description |
|--------|-------------|
| `-f`, `--feature TEXT` | Feature to clean up (required unless `--all` is specified) |
| `--all` | Clean up all MAHABHARATHA features |
| `--keep-logs` | Preserve log files for post-mortem analysis |
| `--keep-branches` | Preserve git branches for manual inspection |
| `--dry-run` | Show the cleanup plan without executing |

## Examples

```bash
# Clean up a specific feature
/mahabharatha:cleanup --feature user-auth

# Preview what will be cleaned
/mahabharatha:cleanup --all --dry-run

# Clean all features
/mahabharatha:cleanup --all

# Keep logs for debugging
/mahabharatha:cleanup --feature user-auth --keep-logs

# Keep branches for inspection
/mahabharatha:cleanup --feature user-auth --keep-branches
```

## Dry Run

Always preview before cleaning:

```bash
/mahabharatha:cleanup --all --dry-run
```

The dry run output lists every resource that would be removed, grouped by category (worktrees, branches, containers, state files, log files), with item counts.

## Recovery

### Before Cleanup

If you might need to resume later:

```bash
# Check status first
/mahabharatha:status

# Export logs
/mahabharatha:logs --json > feature-logs.jsonl

# Backup state
cp .mahabharatha/state/<feature>.json feature-backup.json
```

### After Accidental Cleanup

Git branches can be recovered from the reflog for up to 30 days:

```bash
# Find the deleted branch
git reflog | grep "mahabharatha/<feature>"

# Recover the branch
git checkout -b mahabharatha/<feature>/worker-0 <commit-hash>
```

Worktrees must be recreated by running `/mahabharatha:kurukshetra` again.

## Safety Features

1. **Dry run support** -- Preview shows exact resources before removal.
2. **Confirmation prompt** -- Interactive confirmation before executing.
3. **Feature required** -- Must specify `--feature` or `--all` explicitly.
4. **Spec preservation** -- Design documents and requirements are never deleted.
5. **Task archival** -- Task history is archived before removal.
6. **Git reflog** -- Deleted branches remain recoverable for 30 days.

## See Also

- [[mahabharatha-status]] -- Verify completion before cleanup
- [[mahabharatha-logs]] -- Export logs before cleanup
- [[mahabharatha-stop]] -- Stop workers before cleanup if still running
- [[mahabharatha-Reference]] -- Full command index
