# /mahabharatha:build

Build orchestration with automatic build system detection and error recovery.

## Synopsis

```
/mahabharatha:build [--target all]
            [--mode dev|staging|prod]
            [--clean]
            [--watch]
            [--retry 3]
```

## Description

The `build` command orchestrates project builds with intelligent auto-detection of the build system in use. It inspects the project root for known manifest files and selects the appropriate build toolchain automatically.

When a build fails, MAHABHARATHA classifies the error and attempts recovery actions such as installing missing dependencies, suggesting type error fixes, reducing parallelism for resource exhaustion, or retrying with exponential backoff on network timeouts.

### Supported Build Systems

| Manifest File | Build System |
|---------------|-------------|
| `package.json` | npm |
| `Cargo.toml` | cargo |
| `Makefile` | make |
| `build.gradle` | gradle |
| `go.mod` | go |
| `pyproject.toml` | python |

### Error Recovery

| Error Category | Recovery Action |
|----------------|----------------|
| `missing_dependency` | Install dependencies automatically |
| `type_error` | Suggest a fix for the type mismatch |
| `resource_exhaustion` | Reduce parallelism and retry |
| `network_timeout` | Retry with exponential backoff |

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--target` | `all` | Build target to execute. |
| `--mode` | `dev` | Build mode. Accepts `dev`, `staging`, or `prod`. |
| `--clean` | off | Perform a clean build, removing cached artifacts first. |
| `--watch` | off | Enable watch mode for continuous rebuilds on file changes. |
| `--retry` | `3` | Number of retry attempts on transient build failures. |

## Examples

Build the project using auto-detected defaults:

```
/mahabharatha:build
```

Run a production build:

```
/mahabharatha:build --mode prod
```

Perform a clean build to eliminate stale artifacts:

```
/mahabharatha:build --clean
```

Enable watch mode for iterative development:

```
/mahabharatha:build --watch
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Build successful |
| 1 | Build failed |
| 2 | Configuration error |

## Task Tracking

This command creates a Claude Code Task with the subject prefix `[Build]` on invocation, updates it to `in_progress` immediately, and marks it `completed` on success.

## See Also

- [[mahabharatha-test]] -- Run tests after a successful build
- [[mahabharatha-analyze]] -- Static analysis and quality checks
- [[mahabharatha-review]] -- Code review workflow
