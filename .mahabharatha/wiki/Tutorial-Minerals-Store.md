# Tutorial: Building a Minerals Store with MAHABHARATHA

This tutorial walks through building a hypothetical "minerals store" e-commerce feature using MAHABHARATHA. You will plan requirements, generate a task graph, launch parallel workers, and merge the results.

The minerals store allows users to browse mineral products (vespene gas, crystal shards, rare ores), add them to a cart, and check out. It includes a product catalog API, a shopping cart service, and an order processing pipeline.

## Table of Contents

- [Phase 1: Plan](#phase-1-plan)
- [Phase 2: Design](#phase-2-design)
- [Phase 3: Kurukshetra](#phase-3-kurukshetra)
- [Phase 4: Merge](#phase-4-merge)
- [Phase 5: Verify](#phase-5-verify)
- [Troubleshooting](#troubleshooting)

---

## Phase 1: Plan

Start by capturing requirements. Run the plan command inside a Claude Code session:

```
/mahabharatha:plan minerals-store
```

MAHABHARATHA creates the spec directory and enters planning mode:

```
Created .gsd/specs/minerals-store/
Set current feature: minerals-store
```

### Requirements Discovery

The planner reads your project files and asks clarifying questions. Answer them to define the scope. For this tutorial, assume the following conversation:

```
MAHABHARATHA: What problem does the minerals store solve for users?
YOU:  Users need to browse and purchase mineral products through a REST API.

MAHABHARATHA: What are the core entities and their relationships?
YOU:  Products (name, price, category, stock), Cart (user_id, items),
      Orders (user_id, items, total, status). A cart becomes an order at checkout.

MAHABHARATHA: What are the non-functional requirements?
YOU:  Response time under 200ms for catalog reads. PostgreSQL for storage.
      Python with FastAPI. No authentication for this phase -- add later.
```

### Generated Requirements

After the conversation, MAHABHARATHA writes `.gsd/specs/minerals-store/requirements.md`:

```markdown
# Requirements: minerals-store

## Metadata
- **Feature**: minerals-store
- **Status**: REVIEW
- **Created**: 2026-01-31T10:00:00-05:00

## 1. Problem Statement
Users need a REST API to browse mineral products, manage a shopping cart,
and place orders.

## 2. Functional Requirements

### FR-1: Product Catalog
- List all products with filtering by category
- Get product details by ID
- Categories: crystal, gas, ore

### FR-2: Shopping Cart
- Add/remove items to a cart identified by user_id
- View cart contents with calculated totals
- Clear cart

### FR-3: Order Processing
- Create order from cart contents
- Validate stock availability before order creation
- Deduct stock on successful order
- Return order confirmation with total

## 3. Non-Functional Requirements
- Response time: < 200ms for GET endpoints
- Database: PostgreSQL with SQLAlchemy
- Framework: FastAPI
- No authentication (deferred to future feature)

## 4. Scope Boundaries
- **In scope**: CRUD for products, cart, orders
- **Out of scope**: Payment processing, user auth, admin UI

## 5. Acceptance Criteria
- All endpoints return correct HTTP status codes
- Stock cannot go negative after order placement
- Cart totals match sum of item prices * quantities
```

Review the requirements and approve them:

```
YOU: APPROVED
```

MAHABHARATHA updates the status to APPROVED and marks the planning task as complete.

---

## Phase 2: Design

With approved requirements, generate the architecture and task graph:

```
/mahabharatha:design
```

MAHABHARATHA reads the requirements, analyzes the codebase, and produces two artifacts:

1. `.gsd/specs/minerals-store/design.md` -- architecture document
2. `.gsd/specs/minerals-store/task-graph.json` -- parallelizable task graph

### Architecture Overview

The design document includes a component diagram:

```
                    +-----------------+
                    |   FastAPI App   |
                    +--------+--------+
                             |
            +----------------+----------------+
            |                |                |
   +--------v------+ +------v-------+ +------v--------+
   | Product Router| | Cart Router  | | Order Router  |
   +--------+------+ +------+-------+ +------+--------+
            |                |                |
   +--------v------+ +------v-------+ +------v--------+
   | Product Svc   | | Cart Svc     | | Order Svc     |
   +--------+------+ +------+-------+ +------+--------+
            |                |                |
            +----------------+----------------+
                             |
                    +--------v--------+
                    |   Database      |
                    |  (PostgreSQL)   |
                    +-----------------+
```

### File Ownership Matrix

Each task owns specific files. No two tasks write to the same file:

| File | Task | Operation |
|------|------|-----------|
| `src/minerals/types.py` | TASK-001 | create |
| `src/minerals/models.py` | TASK-002 | create |
| `src/minerals/database.py` | TASK-003 | create |
| `src/minerals/product_service.py` | TASK-004 | create |
| `src/minerals/cart_service.py` | TASK-005 | create |
| `src/minerals/order_service.py` | TASK-006 | create |
| `src/minerals/product_router.py` | TASK-007 | create |
| `src/minerals/cart_router.py` | TASK-008 | create |
| `src/minerals/order_router.py` | TASK-009 | create |
| `src/minerals/app.py` | TASK-010 | create |
| `tests/test_product_service.py` | TASK-011 | create |
| `tests/test_cart_service.py` | TASK-012 | create |
| `tests/test_order_service.py` | TASK-013 | create |

### Task Graph

The generated `task-graph.json` organizes work into levels:

```json
{
  "feature": "minerals-store",
  "version": "2.0",
  "generated": "2026-01-31T10:15:00-05:00",
  "total_tasks": 13,
  "estimated_duration_minutes": 120,
  "max_parallelization": 3,

  "tasks": [
    {
      "id": "TASK-001",
      "title": "Create domain types and schemas",
      "description": "Define Pydantic models for Product, CartItem, Cart, Order, and API request/response schemas.",
      "phase": "foundation",
      "level": 1,
      "dependencies": [],
      "files": {
        "create": ["src/minerals/types.py"],
        "modify": [],
        "read": []
      },
      "verification": {
        "command": "python -c \"from src.minerals.types import Product, Cart, Order\"",
        "timeout_seconds": 30
      },
      "estimate_minutes": 10
    },
    {
      "id": "TASK-002",
      "title": "Create SQLAlchemy models",
      "description": "Define ORM models for products, carts, cart_items, and orders tables.",
      "phase": "foundation",
      "level": 1,
      "dependencies": [],
      "files": {
        "create": ["src/minerals/models.py"],
        "modify": [],
        "read": []
      },
      "verification": {
        "command": "python -c \"from src.minerals.models import ProductModel, CartModel, OrderModel\"",
        "timeout_seconds": 30
      },
      "estimate_minutes": 15
    },
    {
      "id": "TASK-003",
      "title": "Create database connection module",
      "description": "Set up async SQLAlchemy engine, session factory, and Base declarative class.",
      "phase": "foundation",
      "level": 1,
      "dependencies": [],
      "files": {
        "create": ["src/minerals/database.py"],
        "modify": [],
        "read": []
      },
      "verification": {
        "command": "python -c \"from src.minerals.database import get_session, engine\"",
        "timeout_seconds": 30
      },
      "estimate_minutes": 10
    },
    {
      "id": "TASK-004",
      "title": "Implement product service",
      "description": "Business logic for listing, filtering, and retrieving products.",
      "phase": "core",
      "level": 2,
      "dependencies": ["TASK-001", "TASK-002", "TASK-003"],
      "files": {
        "create": ["src/minerals/product_service.py"],
        "modify": [],
        "read": ["src/minerals/types.py", "src/minerals/models.py", "src/minerals/database.py"]
      },
      "verification": {
        "command": "python -c \"from src.minerals.product_service import ProductService\"",
        "timeout_seconds": 30
      },
      "estimate_minutes": 20
    },
    {
      "id": "TASK-005",
      "title": "Implement cart service",
      "description": "Business logic for adding/removing cart items and calculating totals.",
      "phase": "core",
      "level": 2,
      "dependencies": ["TASK-001", "TASK-002", "TASK-003"],
      "files": {
        "create": ["src/minerals/cart_service.py"],
        "modify": [],
        "read": ["src/minerals/types.py", "src/minerals/models.py", "src/minerals/database.py"]
      },
      "verification": {
        "command": "python -c \"from src.minerals.cart_service import CartService\"",
        "timeout_seconds": 30
      },
      "estimate_minutes": 20
    },
    {
      "id": "TASK-006",
      "title": "Implement order service",
      "description": "Business logic for creating orders from carts, stock validation, and stock deduction.",
      "phase": "core",
      "level": 2,
      "dependencies": ["TASK-001", "TASK-002", "TASK-003"],
      "files": {
        "create": ["src/minerals/order_service.py"],
        "modify": [],
        "read": ["src/minerals/types.py", "src/minerals/models.py", "src/minerals/database.py"]
      },
      "verification": {
        "command": "python -c \"from src.minerals.order_service import OrderService\"",
        "timeout_seconds": 30
      },
      "estimate_minutes": 25
    },
    {
      "id": "TASK-007",
      "title": "Create product API router",
      "description": "FastAPI router with GET /products and GET /products/{id} endpoints.",
      "phase": "integration",
      "level": 3,
      "dependencies": ["TASK-004"],
      "files": {
        "create": ["src/minerals/product_router.py"],
        "modify": [],
        "read": ["src/minerals/product_service.py", "src/minerals/types.py"]
      },
      "verification": {
        "command": "python -c \"from src.minerals.product_router import router\"",
        "timeout_seconds": 30
      },
      "estimate_minutes": 15
    },
    {
      "id": "TASK-008",
      "title": "Create cart API router",
      "description": "FastAPI router with POST/GET/DELETE endpoints for cart management.",
      "phase": "integration",
      "level": 3,
      "dependencies": ["TASK-005"],
      "files": {
        "create": ["src/minerals/cart_router.py"],
        "modify": [],
        "read": ["src/minerals/cart_service.py", "src/minerals/types.py"]
      },
      "verification": {
        "command": "python -c \"from src.minerals.cart_router import router\"",
        "timeout_seconds": 30
      },
      "estimate_minutes": 15
    },
    {
      "id": "TASK-009",
      "title": "Create order API router",
      "description": "FastAPI router with POST /orders (checkout) and GET /orders/{id} endpoints.",
      "phase": "integration",
      "level": 3,
      "dependencies": ["TASK-006"],
      "files": {
        "create": ["src/minerals/order_router.py"],
        "modify": [],
        "read": ["src/minerals/order_service.py", "src/minerals/types.py"]
      },
      "verification": {
        "command": "python -c \"from src.minerals.order_router import router\"",
        "timeout_seconds": 30
      },
      "estimate_minutes": 15
    },
    {
      "id": "TASK-010",
      "title": "Create FastAPI application entry point",
      "description": "Wire all routers into the FastAPI app with middleware and error handlers.",
      "phase": "integration",
      "level": 3,
      "dependencies": ["TASK-007", "TASK-008", "TASK-009"],
      "files": {
        "create": ["src/minerals/app.py"],
        "modify": [],
        "read": [
          "src/minerals/product_router.py",
          "src/minerals/cart_router.py",
          "src/minerals/order_router.py"
        ]
      },
      "verification": {
        "command": "python -c \"from src.minerals.app import app\"",
        "timeout_seconds": 30
      },
      "estimate_minutes": 10
    },
    {
      "id": "TASK-011",
      "title": "Write product service tests",
      "description": "Unit tests for product listing, filtering by category, and retrieval by ID.",
      "phase": "testing",
      "level": 4,
      "dependencies": ["TASK-004"],
      "files": {
        "create": ["tests/test_product_service.py"],
        "modify": [],
        "read": ["src/minerals/product_service.py"]
      },
      "verification": {
        "command": "pytest tests/test_product_service.py -v",
        "timeout_seconds": 60
      },
      "estimate_minutes": 15
    },
    {
      "id": "TASK-012",
      "title": "Write cart service tests",
      "description": "Unit tests for adding/removing items, total calculation, and cart clearing.",
      "phase": "testing",
      "level": 4,
      "dependencies": ["TASK-005"],
      "files": {
        "create": ["tests/test_cart_service.py"],
        "modify": [],
        "read": ["src/minerals/cart_service.py"]
      },
      "verification": {
        "command": "pytest tests/test_cart_service.py -v",
        "timeout_seconds": 60
      },
      "estimate_minutes": 15
    },
    {
      "id": "TASK-013",
      "title": "Write order service tests",
      "description": "Unit tests for order creation, stock validation, and stock deduction.",
      "phase": "testing",
      "level": 4,
      "dependencies": ["TASK-006"],
      "files": {
        "create": ["tests/test_order_service.py"],
        "modify": [],
        "read": ["src/minerals/order_service.py"]
      },
      "verification": {
        "command": "pytest tests/test_order_service.py -v",
        "timeout_seconds": 60
      },
      "estimate_minutes": 20
    }
  ],

  "levels": {
    "1": {
      "name": "foundation",
      "tasks": ["TASK-001", "TASK-002", "TASK-003"],
      "parallel": true,
      "estimated_minutes": 15
    },
    "2": {
      "name": "core",
      "tasks": ["TASK-004", "TASK-005", "TASK-006"],
      "parallel": true,
      "estimated_minutes": 25
    },
    "3": {
      "name": "integration",
      "tasks": ["TASK-007", "TASK-008", "TASK-009", "TASK-010"],
      "parallel": true,
      "estimated_minutes": 15
    },
    "4": {
      "name": "testing",
      "tasks": ["TASK-011", "TASK-012", "TASK-013"],
      "parallel": true,
      "estimated_minutes": 20
    }
  },

  "conflict_matrix": {
    "description": "No file conflicts -- all tasks have exclusive ownership",
    "conflicts": []
  }
}
```

### Dependency Graph

The task dependencies form a directed acyclic graph:

```
Level 1 (foundation)     Level 2 (core)        Level 3 (integration)     Level 4 (testing)
+------------+
| TASK-001   |--------+---> TASK-004 -----> TASK-007 --+
| types.py   |        |    product_svc     product_rtr |  +-> TASK-011
+------------+        |                                |  |   product_tests
                      +---> TASK-005 -----> TASK-008 --+--+
+------------+        |    cart_svc        cart_rtr     |  +-> TASK-012
| TASK-002   |--------+                                |  |   cart_tests
| models.py  |        +---> TASK-006 -----> TASK-009 --+--+
+------------+        |    order_svc       order_rtr   |  +-> TASK-013
                      |                                |      order_tests
+------------+        |                    TASK-010 <---+
| TASK-003   |--------+                    app.py
| database.py|
+------------+
```

Note that TASK-010 (the app entry point) depends on TASK-007, TASK-008, and TASK-009 since it imports all three routers. The design phase detects this and places it at Level 3 but scheduled after the routers complete.

### Approval

Review the design and approve:

```
YOU: approved
```

MAHABHARATHA registers all 13 tasks in the Claude Code Task system with `[L1]`, `[L2]`, `[L3]`, and `[L4]` subject prefixes.

---

## Phase 3: Kurukshetra

Launch the akshauhini. Three workers are optimal for this task graph since the widest level has three parallel tasks:

```
/mahabharatha:kurukshetra --workers=3
```

### What Happens

MAHABHARATHA performs these steps automatically:

**Step 1 -- Analyze task graph**

```
Task graph loaded: 13 tasks across 4 levels
Max parallelization: 3
Adjusting worker count to 3 (matches max parallelization)
```

**Step 2 -- Create git worktrees**

```
Creating worktree: ../.mahabharatha-worktrees/minerals-store/worker-0
Creating worktree: ../.mahabharatha-worktrees/minerals-store/worker-1
Creating worktree: ../.mahabharatha-worktrees/minerals-store/worker-2
```

**Step 3 -- Assign tasks to workers**

The orchestrator distributes tasks evenly across workers:

| Worker | Level 1 | Level 2 | Level 3 | Level 4 |
|--------|---------|---------|---------|---------|
| 0 | TASK-001 | TASK-004 | TASK-007 | TASK-011 |
| 1 | TASK-002 | TASK-005 | TASK-008 | TASK-012 |
| 2 | TASK-003 | TASK-006 | TASK-009, TASK-010 | TASK-013 |

Worker 2 gets TASK-010 in addition to TASK-009 because it depends on all three routers and must execute after them.

**Step 4 -- Launch workers**

```
Launching Worker 0 on branch mahabharatha/minerals-store/worker-0...
Launching Worker 1 on branch mahabharatha/minerals-store/worker-1...
Launching Worker 2 on branch mahabharatha/minerals-store/worker-2...
Orchestrator started (PID 48201)
```

### Monitoring Progress

Open a separate terminal and run:

```bash
mahabharatha status --watch --interval 2
```

Output updates every 2 seconds:

```
MAHABHARATHA STATUS: minerals-store
===========================================================

Level 1 (foundation)                          [ACTIVE]
  TASK-001  Create domain types       worker-0  IN_PROGRESS
  TASK-002  Create SQLAlchemy models  worker-1  IN_PROGRESS
  TASK-003  Create database module    worker-2  IN_PROGRESS

Level 2 (core)                                [PENDING]
  TASK-004  Product service           worker-0  PENDING
  TASK-005  Cart service              worker-1  PENDING
  TASK-006  Order service             worker-2  PENDING

Level 3 (integration)                         [PENDING]
  TASK-007  Product router            worker-0  PENDING
  TASK-008  Cart router               worker-1  PENDING
  TASK-009  Order router              worker-2  PENDING
  TASK-010  App entry point           worker-2  PENDING

Level 4 (testing)                             [PENDING]
  TASK-011  Product tests             worker-0  PENDING
  TASK-012  Cart tests                worker-1  PENDING
  TASK-013  Order tests               worker-2  PENDING

Workers: 3 active | Tasks: 3/13 in progress
```

After Level 1 completes, you will see:

```
Level 1 (foundation)                          [COMPLETE]
  TASK-001  Create domain types       worker-0  COMPLETE
  TASK-002  Create SQLAlchemy models  worker-1  COMPLETE
  TASK-003  Create database module    worker-2  COMPLETE

  Merge: Level 1 merged successfully (commit a3f8c21)
  Quality gates: lint OK | typecheck OK | test OK

Level 2 (core)                                [ACTIVE]
  TASK-004  Product service           worker-0  IN_PROGRESS
  TASK-005  Cart service              worker-1  IN_PROGRESS
  TASK-006  Order service             worker-2  IN_PROGRESS
```

### Worker Execution Detail

Each worker follows the same protocol. Here is what Worker 0 does for TASK-004:

1. Claims the task by calling `TaskUpdate` with `status: "in_progress"`
2. Reads `types.py`, `models.py`, and `database.py` from the merged Level 1 output
3. Creates `src/minerals/product_service.py` following the design document
4. Runs the verification command: `python -c "from src.minerals.product_service import ProductService"`
5. If verification passes, commits the file with metadata:
   ```
   feat(minerals-store): Implement product service

   Task-ID: TASK-004
   Worker: 0
   Verified: python -c "from src.minerals.product_service import ProductService"
   Level: 2
   ```
6. Calls `TaskUpdate` with `status: "completed"`

### Level Transitions

After all workers complete a level:

1. The orchestrator triggers `/mahabharatha:merge` for that level
2. Worker branches are merged into a staging branch
3. Quality gates run (lint, typecheck, test)
4. If gates pass, worker branches are rebased onto the merged result
5. Workers proceed to the next level

This repeats for each level until all tasks are done.

---

## Phase 4: Merge

Merging happens automatically during kurukshetra, but you can also trigger it manually. If you need to merge Level 2 explicitly:

```
/mahabharatha:merge --level 2
```

### Merge Output

```
MAHABHARATHA MERGE
===========================================================

Feature: minerals-store
Level: 2 of 4
Status: Ready for merge

Worker Branches:
+-----------+-------------------------------------+----------+----------+
| Worker    | Branch                              | Commits  | Status   |
+-----------+-------------------------------------+----------+----------+
| worker-0  | mahabharatha/minerals-store/worker-0        | 1        | Ready    |
| worker-1  | mahabharatha/minerals-store/worker-1        | 1        | Ready    |
| worker-2  | mahabharatha/minerals-store/worker-2        | 1        | Ready    |
+-----------+-------------------------------------+----------+----------+

Merge Progress:
[1/5] Creating staging branch... OK
[2/5] Merging worker-0... OK
[3/5] Merging worker-1... OK
[4/5] Merging worker-2... OK
[5/5] Running quality gates...
      - lint: OK
      - typecheck: OK
      - test: OK

===========================================================
Level 2 merge complete!

Merge commit: b7e4f19
Tag: mahabharatha/minerals-store/level-2-complete

Next: Level 3 tasks are now unblocked.
===========================================================
```

### What If Quality Gates Fail?

If the lint or test gate fails after a merge, MAHABHARATHA reports the failure and stops progression:

```
[5/5] Running quality gates...
      - lint: FAILED
        src/minerals/order_service.py:42:1: E302 expected 2 blank lines
      - typecheck: OK
      - test: OK

Quality gates failed: lint
Aborting merge. Fix issues or use --force
```

At this point you have two options:

1. Fix the issue manually on the staging branch and re-run the merge
2. Use `mahabharatha retry TASK-006 --on-base` to re-execute the failing task against the merged base

---

## Phase 5: Verify

After all four levels complete, check the final state:

```
/mahabharatha:status
```

```
MAHABHARATHA STATUS: minerals-store
===========================================================

Feature: minerals-store
Status: COMPLETE

Level 1 (foundation)   [COMPLETE]  3/3 tasks  merged: a3f8c21
Level 2 (core)         [COMPLETE]  3/3 tasks  merged: b7e4f19
Level 3 (integration)  [COMPLETE]  4/4 tasks  merged: c92d501
Level 4 (testing)      [COMPLETE]  3/3 tasks  merged: d15ea38

Total: 13/13 tasks complete
Duration: 18 minutes (estimated sequential: 55 minutes)
Speedup: 3.1x with 3 workers

Final branch: mahabharatha/minerals-store/staging-level-4
```

The feature is now on the staging branch. To bring it into your main branch:

```bash
git checkout main
git merge mahabharatha/minerals-store/staging-level-4 --no-ff -m "feat: minerals store e-commerce feature"
```

### Cleanup

Remove the worktrees and temporary branches:

```
/mahabharatha:cleanup minerals-store
```

This removes:

- Git worktrees in `../.mahabharatha-worktrees/minerals-store/`
- Worker branches `mahabharatha/minerals-store/worker-*`
- State files in `.mahabharatha/state/`
- Completed tasks from the Claude Code Task system

---

## Troubleshooting

### Worker stuck on a task

Check the worker log:

```bash
cat .mahabharatha/logs/workers/worker-0.stdout.log
```

If a worker hit its context limit (70%), it exits with code 2 and the orchestrator restarts it. Check the progress file:

```bash
cat .gsd/specs/minerals-store/progress.md
```

### Merge conflicts

MAHABHARATHA prevents merge conflicts through exclusive file ownership. If you see a conflict, it usually means the task graph has a bug where two tasks modify the same file. Re-run `/mahabharatha:design` to regenerate the graph.

### Verification command fails

Each task has a verification command in the task graph. If it fails, the worker retries up to 3 times with different approaches. After 3 failures, the task is marked as BLOCKED. Use `/mahabharatha:retry TASK-ID` to reset and re-attempt.

### Workers not starting

Confirm your Claude Code authentication is valid:

```bash
claude --version
```

Check that git worktrees were created:

```bash
ls -la ../.mahabharatha-worktrees/minerals-store/
```

---

## Summary

This tutorial demonstrated the full MAHABHARATHA workflow:

1. `/mahabharatha:plan minerals-store` -- captured requirements through structured conversation
2. `/mahabharatha:design` -- generated architecture, file ownership matrix, and a 13-task graph across 4 levels
3. `/mahabharatha:kurukshetra --workers=3` -- launched 3 parallel workers executing tasks level by level
4. Automatic merging with quality gates after each level
5. Final verification showing 3.1x speedup over sequential execution

The key concepts that made parallel execution safe:

- **Exclusive file ownership** prevented merge conflicts
- **Level-based ordering** respected dependencies between tasks
- **Verification commands** caught errors at the task level before merging
- **Quality gates** caught integration issues after merging each level

Next tutorial: [[Tutorial-Container-Mode]] for isolated Docker-based execution.
