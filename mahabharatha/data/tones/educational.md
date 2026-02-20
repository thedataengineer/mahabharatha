# Educational Tone

**Default tone for `/mahabharatha:document`.**

Teaches "why" not just "what". Every concept gets a plain-language explanation, a narrative connecting it to the bigger picture, a Mermaid diagram, and concrete CLI examples.

## When to Use

- New users learning Mahabharatha for the first time
- Onboarding documentation
- Concept-heavy components where understanding matters more than quick reference
- Any documentation where the reader needs to understand the reasoning behind design decisions

## Required Sections Per Concept

Every concept or component documented in this tone MUST include these four sections:

### CONCEPT

A plain-language explanation of what this thing is and why it exists. No jargon without definition. Answer: "What problem does this solve?"

- Start with a one-sentence summary
- Explain the problem it addresses
- Define any domain-specific terms
- State the key insight or principle

### NARRATIVE

Connect this concept to the bigger picture. How does it fit into the overall system? What comes before and after it in the workflow?

- Explain the context: what triggers this, what depends on it
- Describe the relationship to other components
- Use analogies where helpful
- Keep it conversational but precise

### DIAGRAM

A Mermaid diagram showing the concept's relationships, data flow, or lifecycle.

- Use `graph TD` for dependency/flow diagrams
- Use `sequenceDiagram` for interaction sequences
- Use `stateDiagram-v2` for state transitions
- Keep diagrams focused (5-10 nodes max)
- Label edges with action descriptions

### COMMAND

Concrete CLI examples showing how to use or interact with this concept.

- Show the most common usage first
- Include expected output where helpful
- Show at least one variation or option
- Use real file paths from the project, not placeholders

## Output Structure Template

```markdown
# {Component Title}

> One-sentence summary of what this component does.

## CONCEPT

{Plain-language explanation of what this is and why it exists.}

## NARRATIVE

{How this fits into the bigger picture. What comes before/after. Relationships.}

## DIAGRAM

```mermaid
graph TD
    A["{Related Component}"] --> B["{This Component}"]
    B --> C["{Downstream Component}"]


    %% Visual Styles
    classDef default fill:#F9FAFB,stroke:#D1D5DB,stroke-width:2px,color:#111827;
    classDef highlight fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px,color:#1D4ED8;
    classDef success fill:#ECFDF5,stroke:#10B981,stroke-width:2px,color:#047857;
    classDef warning fill:#FFFBEB,stroke:#F59E0B,stroke-width:2px,color:#B45309;
    classDef error fill:#FEF2F2,stroke:#EF4444,stroke-width:2px,color:#B91C1C;
```

## COMMAND

```bash
# Primary usage
{command example}

# With options
{command example with flags}
```

---

{Repeat CONCEPT/NARRATIVE/DIAGRAM/COMMAND for each additional concept in the component.}
```

## Example Output

```markdown
# Mahabharatha Launcher

> Spawns and manages parallel Claude Code worker processes.

## CONCEPT

The Launcher is Mahabharatha's process manager. When you run `/mahabharatha:Kurukshetra`, the Launcher takes the task graph and spawns one Claude Code instance per worker, each in its own git worktree. It handles three execution modes: Task (in-process subagents), Subprocess (local Python processes), and Container (Docker containers).

Think of it as a foreman on a construction site: it assigns workers to tasks, makes sure they have the right tools, and reports back when they finish.

## NARRATIVE

The Launcher sits between the Orchestrator (which decides what to build) and the Workers (which do the building). After `/mahabharatha:design` produces a task-graph.json, and `/mahabharatha:Kurukshetra` triggers execution, the Orchestrator calls the Launcher to spawn workers for each level.

The Launcher is the only component that interacts with the operating system to create processes. Everything upstream is pure planning; everything downstream is pure execution.

## DIAGRAM

```mermaid
graph TD
    O["Orchestrator"] -->|"spawn(task, mode)"| L["Launcher"]
    L -->|"Task mode"| T["Task Tool Subagent"]
    L -->|"Subprocess mode"| S["Python Process"]
    L -->|"Container mode"| D["Docker Container"]
    T --> W["Worker Execution"]
    S --> W
    D --> W


    %% Visual Styles
    classDef default fill:#F9FAFB,stroke:#D1D5DB,stroke-width:2px,color:#111827;
    classDef highlight fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px,color:#1D4ED8;
    classDef success fill:#ECFDF5,stroke:#10B981,stroke-width:2px,color:#047857;
    classDef warning fill:#FFFBEB,stroke:#F59E0B,stroke-width:2px,color:#B45309;
    classDef error fill:#FEF2F2,stroke:#EF4444,stroke-width:2px,color:#B91C1C;
```

## COMMAND

```bash
# Default: Task mode (in-process subagents)
/mahabharatha:Kurukshetra --workers 5

# Subprocess mode
/mahabharatha:Kurukshetra --workers 3 --mode subprocess

# Container mode (requires Docker)
/mahabharatha:Kurukshetra --workers 5 --mode container
```
```
