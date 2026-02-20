# /mahabharatha:hooks

Install or check MAHABHARATHA pre-commit hooks.

## Usage

```bash
# Install hooks to .git/hooks/
mahabharatha hooks install

# Check hook status
mahabharatha hooks status

# Run hooks manually on staged files
mahabharatha hooks run

# Uninstall hooks
mahabharatha hooks uninstall
```

## What the Hook Checks

### Security (Blocks Commit)

| Pattern | Description |
|---------|-------------|
| `AKIA[0-9A-Z]{16}` | AWS Access Key |
| `ghp_[a-zA-Z0-9]{36}` | GitHub PAT (classic) |
| `github_pat_...` | GitHub PAT (fine-grained) |
| `sk-[a-zA-Z0-9]{48}` | OpenAI API Key |
| `sk-ant-...` | Anthropic API Key |
| `-----BEGIN * PRIVATE KEY-----` | Private key headers |
| `shell=True`, `os.system()` | Shell injection |
| `eval()`, `exec()` | Code injection |
| `pickle.load()` | Unsafe deserialization |
| `.env`, `credentials.json` | Sensitive files |

### Quality (Warns Only)

| Check | Trigger |
|-------|---------|
| Ruff lint | Staged Python files |
| Debugger | `breakpoint()`, `pdb.set_trace()` |
| Merge markers | `<<<<<<<`, `=======`, `>>>>>>>` |
| Large files | >5MB |

### MAHABHARATHA-Specific (Warns Only)

| Check | Validation |
|-------|------------|
| Branch naming | `mahabharatha/{feature}/worker-{N}` |
| Print statements | `print()` in `mahabharatha/` directory |
| Hardcoded localhost | `localhost:PORT` outside tests |

## Exempt Paths

- `tests/`
- `fixtures/`
- `*_test.py`, `test_*.py`
- `conftest.py`

## Configuration

In `.mahabharatha/config.yaml`:

```yaml
hooks:
  pre_commit:
    enabled: true
    security_checks:
      secrets_detection: true
      shell_injection: true
      block_on_violation: true
    quality_checks:
      ruff_lint: true
      warn_on_violation: true
```

## Related

- `mahabharatha/security.py`: HOOK_PATTERNS definitions
- `.mahabharatha/hooks/pre-commit`: Hook script
- `tests/unit/test_hooks.py`: Pattern tests
