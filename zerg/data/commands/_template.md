# ZERG {CommandName}

<!-- Replace with a one-line description of what this command does. -->
{Short description of the command's purpose.}

## Usage

```bash
/zerg:{command-name} [--flag-a <value>]
                     [--flag-b]
                     [--help]
```

## Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--flag-a` | `none` | {What this flag controls} |
| `--flag-b` | `false` | {What this flag enables} |
| `--help` | | Show usage and exit |

## Pre-flight

<!-- Replace with checks your command needs before running. -->
```bash
# Example: verify required tools or state files exist
test -f .zerg/config.yaml || echo "Run /zerg:init first"
```

## Task Tracking

On invocation, create a Claude Code Task to track this command:

Call TaskCreate:
  - subject: "[{CommandName}] {action} {target}"
  - description: "{Description of what this command does}. {Additional context}."
  - activeForm: "{Present continuous form of the action}"

Immediately call TaskUpdate:
  - taskId: (the Claude Task ID)
  - status: "in_progress"

On completion, call TaskUpdate:
  - taskId: (the Claude Task ID)
  - status: "completed"

## Execution

<!-- Replace with the command's main logic. -->
1. {First step of command execution}
2. {Second step}
3. {Final step or output}

## Exit Codes

- 0: {Command} successful
- 1: {Command} failed
- 2: Configuration error

## Help

When `--help` is passed in `$ARGUMENTS`, display usage and exit:

```
/zerg:{command-name} -- {Short description}.

Flags:
  --flag-a <value>  {What this flag controls}
  --flag-b          {What this flag enables}
  --help            Show this help message
```
