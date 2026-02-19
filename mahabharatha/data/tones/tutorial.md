# Tutorial Tone

**Step-by-step walkthrough with simulated dialogues and progressive complexity.**

Guides the reader through using a component from zero to proficiency. Shows what to type, what to expect, and what to do when things go wrong.

## When to Use

- Getting-started guides
- Feature walkthroughs for first-time use
- Workflow tutorials that span multiple commands
- Troubleshooting guides where step order matters

## Style Guidelines

- Number every step
- Show the exact command and its expected output
- Build complexity progressively: basic usage first, then options, then advanced
- Include "What you should see" after each command
- Use simulated terminal dialogues to show interactive flows
- Add "Checkpoint" boxes after major milestones
- Include "If something goes wrong" callouts for common failure modes

## Required Sections

### Prerequisites

What the reader needs before starting. Software, configuration, prior knowledge.

### Steps

Numbered sequence of actions. Each step has:
1. What to do (command or action)
2. What you should see (expected output)
3. Why this matters (one sentence)

### Checkpoints

After every 3-5 steps, a verification that the reader is on track.

### Troubleshooting

Common problems and their solutions, tied to specific steps.

## Output Structure Template

```markdown
# Tutorial: {Title}

> {What the reader will learn/accomplish by the end.}

## Prerequisites

- {Requirement 1}
- {Requirement 2}

## Step 1: {Action Title}

{Brief explanation of what we're doing and why.}

```bash
$ {command}
{expected output}
```

## Step 2: {Action Title}

{Brief explanation.}

```bash
$ {command}
{expected output}
```

## Step 3: {Action Title}

{Brief explanation.}

```bash
$ {command}
{expected output}
```

> **Checkpoint**: At this point you should have {verification criteria}. Run `{check command}` to confirm.

## Step 4: {Action Title}

{Now building on the basics...}

```bash
$ {command with options}
{expected output}
```

## Troubleshooting

### "{Error message or symptom}"

**Cause**: {Why this happens.}

**Fix**: {What to do.}

```bash
$ {fix command}
```

## Next Steps

- {What to learn next}
- {Related tutorial}
```

## Example Output

```markdown
# Tutorial: Your First Mahabharatha Rush

> By the end of this tutorial, you'll plan, design, and execute a feature using parallel workers.

## Prerequisites

- Claude Code CLI installed and authenticated
- A git repository with Mahabharatha initialized (`/mahabharatha:init` completed)
- At least 5 minutes of uninterrupted time

## Step 1: Plan the Feature

Every Mahabharatha feature starts with a plan. Tell Mahabharatha what you want to build:

```bash
$ /mahabharatha:plan user-notifications
```

Mahabharatha will ask you clarifying questions about your feature. Answer them — this builds the requirements document.

```
═══════════════════════════════════════════════════════════════
                 REQUIREMENTS READY FOR REVIEW
═══════════════════════════════════════════════════════════════

Feature: user-notifications
Summary:
  - 8 functional requirements (5 must / 2 should / 1 could)
  - 3 test scenarios

Reply with: "APPROVED" or "REJECTED"
═══════════════════════════════════════════════════════════════
```

Type `APPROVED` to lock in the requirements.

## Step 2: Design the Architecture

Now Mahabharatha creates the technical design and task graph:

```bash
$ /mahabharatha:design
```

You'll see the architecture, file ownership matrix, and task dependency graph. Review it carefully — this is the blueprint for parallel execution.

## Step 3: Launch the Swarm

Time to execute. Launch 3 parallel workers:

```bash
$ /mahabharatha:Kurukshetra --workers 3
```

> **Checkpoint**: Run `/mahabharatha:status` to verify all Level 1 tasks are in progress. You should see 3 workers active.

## Step 4: Monitor Progress

While workers execute, check status:

```bash
$ /mahabharatha:status

Feature: user-notifications
Workers: 3 active

Level 1 (foundation): ████████████ 100% [3/3 complete]
Level 2 (core):       ████░░░░░░░░  33% [1/3 in progress]
```

## Troubleshooting

### "ERROR: Task graph not found"

**Cause**: You skipped the design phase.

**Fix**: Run `/mahabharatha:design` first, then retry `/mahabharatha:Kurukshetra`.

### "Worker failed: verification command exit code 1"

**Cause**: The worker's code didn't pass its verification check.

**Fix**: Run `/mahabharatha:retry` to re-attempt failed tasks, or `/mahabharatha:debug {task-id}` to investigate.

## Next Steps

- Learn about container mode: `/mahabharatha:Kurukshetra --mode container`
- Customize quality gates in `.mahabharatha/config.yaml`
- Try `/mahabharatha:review` for automated code review after completion
```
