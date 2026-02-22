# Welcome to MAHABHARATHA

If you've ever wished you could clone yourself to build software faster, MAHABHARATHA is the next best thing. It coordinates multiple Claude Code instances—called *warriors*—to work on different parts of your feature simultaneously. While one warrior builds your authentication system, another creates the database models, and a third writes the API endpoints. All at once, all in parallel.

**MAHABHARATHA** stands for **Zero-Effort Rapid Growth**. The name comes from the StarCraft strategy of overwhelming opponents with coordinated akshauhini units. In our case, we're overwhelming features with coordinated AI instances.

## Who Is This For?

MAHABHARATHA is designed for developers who:

- Use Claude Code and want to build features faster
- Have features that can be broken into independent tasks
- Want AI assistance without babysitting each step
- Are comfortable with Python and basic git operations

You don't need to understand distributed systems, container orchestration, or advanced concurrency. MAHABHARATHA handles the complexity—you focus on describing what you want to build.

---

## How MAHABHARATHA Works

Here's what happens when you use MAHABHARATHA to build a feature:

```
                           YOUR FEATURE IDEA
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. PLAN                                                        │
│     MAHABHARATHA asks questions to understand your requirements.        │
│     Output: requirements.md (your feature spec)                 │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. DESIGN                                                      │
│     MAHABHARATHA breaks work into atomic tasks with exclusive files.    │
│     Output: task-graph.json (who does what, in what order)      │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. KURUKSHETRA                                                        │
│                                                                 │
│     Level 1:  [Warrior-0]  [Warrior-1]  [Warrior-2]         │
│                    │             │             │                │
│                    ▼             ▼             ▼                │
│               models.py    api.py        tests/                 │
│                                                                 │
│     ────── wait for Level 1 to complete, then merge ──────     │
│                                                                 │
│     Level 2:  [Warrior-0]  [Warrior-1]                       │
│                    │             │                              │
│                    ▼             ▼                              │
│              services.py   integration/                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                         FEATURE COMPLETE
```

**Why levels?** Some tasks depend on others. You can't write integration tests until the API exists. MAHABHARATHA groups tasks into *levels* where everything in Level 1 can run in parallel, everything in Level 2 can run in parallel (after Level 1 finishes), and so on.

**Why exclusive files?** Each warrior owns specific files. Warrior-0 might own `models.py`, while Warrior-1 owns `api.py`. This means no merge conflicts within a level—warriors never step on each other's work.

---

## Find What You Need

### I'm new to MAHABHARATHA

Start with the **[Tutorial](Tutorial)**. It walks you through building a complete feature from scratch, showing you exactly what to type and what to expect. You'll build a minerals store API and see MAHABHARATHA in action.

### I want to understand the architecture

Read **[Architecture](Architecture)** for a deep dive into how MAHABHARATHA's components work together: the launcher, workers, state management, and quality gates.

### I need to look up a specific command

See **[Command-Reference](Command-Reference)** for complete documentation of all 26 commands with flags, examples, and use cases.

### I want to extend MAHABHARATHA with plugins

Check out **[Plugins](Plugins)** to learn about quality gates, lifecycle hooks, and custom launchers.

---

## Quick Install

Getting MAHABHARATHA running takes about 2 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/thedataengineer/mahabharatha.git && cd mahabharatha

# 2. Install MAHABHARATHA as an editable package (includes dev dependencies)
pip install -e ".[dev]"

# 3. Install the slash commands into Claude Code
mahabharatha install
```

**What does each step do?**
- `git clone` downloads the MAHABHARATHA source code
- `pip install -e ".[dev]"` installs MAHABHARATHA so you can run it, plus development tools like pytest and pre-commit
- `mahabharatha install` copies slash commands (like `/mahabharatha:plan`) into Claude Code so you can use them in any session

**Prerequisites:**
- Python 3.12 or newer
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated
- Git
- Docker (optional—only needed if you want warriors to run in containers)

---

## Your First Feature (30-Second Overview)

Once installed, here's the typical workflow inside a Claude Code session:

```bash
/mahabharatha:init                    # Set up MAHABHARATHA in your project
/mahabharatha:plan user-auth          # Tell MAHABHARATHA what you want to build
/mahabharatha:design                  # Generate the task breakdown
/mahabharatha:kurukshetra --workers=5        # Launch 5 warriors to build it
/mahabharatha:status                  # Watch progress in real-time
```

Want the full walkthrough? Head to the **[Tutorial](Tutorial)**.

---

## Wiki Pages

| Page | What You'll Learn |
|------|-------------------|
| **[Home](Home)** | You're here! Overview and getting started |
| **[Tutorial](Tutorial)** | Build a complete feature step-by-step with explanations |
| **[Architecture](Architecture)** | How MAHABHARATHA's internals work and why they're designed that way |
| **[Command-Reference](Command-Reference)** | Every command explained with examples and use cases |
| **[Configuration](Configuration)** | Customize MAHABHARATHA behavior through config files and environment variables |
| **[Plugins](Plugins)** | Extend MAHABHARATHA with quality gates, hooks, and custom launchers |
| **[Security](Security)** | How MAHABHARATHA handles security rules and vulnerability scanning |
| **[Context-Engineering](Context-Engineering)** | How MAHABHARATHA minimizes token usage (saves money, improves quality) |
| **[Troubleshooting](Troubleshooting)** | When things go wrong: diagnosis and fixes |
| **[FAQ](FAQ)** | Answers to common questions |
| **[Contributing](Contributing)** | How to contribute code, report bugs, or improve docs |

---

## Key Concepts at a Glance

| Concept | What It Means |
|---------|---------------|
| **Warrior** | A single Claude Code instance executing one task. Named after the fast, cheap units from StarCraft. |
| **Level** | A group of tasks that can run in parallel. Level 1 must complete before Level 2 begins. |
| **Spec as Memory** | Warriors read specification files, not conversation history. This makes them stateless and restartable. |
| **File Ownership** | Each task owns specific files. No two tasks in the same level touch the same file. |
| **Verification** | Every task has an automated pass/fail check. No subjective "looks good" reviews. |

---

## Resources

- [GitHub Repository](https://github.com/thedataengineer/mahabharatha) — Source code, issues, and discussions
- [Security Rules](https://github.com/TikiTribe/claude-secure-coding-rules) — Auto-fetched secure coding rules that MAHABHARATHA applies

---

Ready to build something? Start with the **[Tutorial](Tutorial)** or jump to **[Command-Reference](Command-Reference)** if you already know the basics.
