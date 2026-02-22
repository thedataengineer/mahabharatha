"""MAHABHARATHA worker subprocess entrypoint.

This module provides the CLI entry point for worker subprocesses.
It initializes the worker environment and starts the worker protocol.
"""

import argparse
import os
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="mahabharatha.worker_main",
        description="MAHABHARATHA Worker Subprocess - Execute tasks in parallel",
    )

    parser.add_argument(
        "--worker-id",
        type=int,
        default=int(os.environ.get("MAHABHARATHA_WORKER_ID", "0")),
        help="Worker identifier (default: from MAHABHARATHA_WORKER_ID env)",
    )

    parser.add_argument(
        "--feature",
        type=str,
        default=os.environ.get("MAHABHARATHA_FEATURE", ""),
        help="Feature name (default: from MAHABHARATHA_FEATURE env)",
    )

    parser.add_argument(
        "--worktree",
        type=Path,
        default=Path(os.environ.get("MAHABHARATHA_WORKTREE", ".")),
        help="Path to git worktree (default: from MAHABHARATHA_WORKTREE env or current dir)",
    )

    parser.add_argument(
        "--branch",
        type=str,
        default=os.environ.get("MAHABHARATHA_BRANCH", ""),
        help="Git branch name (default: from MAHABHARATHA_BRANCH env)",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path(".mahabharatha/config.yaml"),
        help="Path to config file (default: .mahabharatha/config.yaml)",
    )

    parser.add_argument(
        "--task-graph",
        type=Path,
        default=None,
        help="Path to task-graph.json (default: auto-detect from feature)",
    )

    parser.add_argument(
        "--assignments",
        type=Path,
        default=None,
        help="Path to worker-assignments.json (default: auto-detect)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate setup without executing tasks",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="MAHABHARATHA Worker 1.0.0",
    )

    return parser.parse_args()


def setup_environment(args: argparse.Namespace) -> dict[str, str]:
    """Set up worker environment variables.

    Args:
        args: Parsed command line arguments

    Returns:
        Environment variables dictionary
    """
    env = os.environ.copy()

    # Set MAHABHARATHA-specific environment
    env["MAHABHARATHA_WORKER_ID"] = str(args.worker_id)
    env["MAHABHARATHA_FEATURE"] = args.feature
    env["MAHABHARATHA_WORKTREE"] = str(args.worktree.resolve())

    if args.branch:
        env["MAHABHARATHA_BRANCH"] = args.branch
    elif not env.get("MAHABHARATHA_BRANCH"):
        env["MAHABHARATHA_BRANCH"] = f"mahabharatha/{args.feature}/worker-{args.worker_id}"

    return env


def validate_setup(args: argparse.Namespace) -> list[str]:
    """Validate worker setup.

    Args:
        args: Parsed arguments

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if not args.feature:
        errors.append("Feature name required (--feature or MAHABHARATHA_FEATURE env)")

    if not args.worktree.exists():
        errors.append(f"Worktree path does not exist: {args.worktree}")

    if args.config and not args.config.exists():
        errors.append(f"Config file not found: {args.config}")

    if args.task_graph and not args.task_graph.exists():
        errors.append(f"Task graph not found: {args.task_graph}")

    return errors


def main() -> int:
    """Main entry point for worker subprocess.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_args()

    # Validate setup
    errors = validate_setup(args)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    # Set up environment
    env = setup_environment(args)
    for key, value in env.items():
        if key.startswith("MAHABHARATHA_"):
            os.environ[key] = value

    # Log cross-cutting capability env vars at startup
    capability_vars = {
        k: v
        for k, v in os.environ.items()
        if k.startswith("MAHABHARATHA_")
        and k
        not in (
            "MAHABHARATHA_WORKER_ID",
            "MAHABHARATHA_FEATURE",
            "MAHABHARATHA_WORKTREE",
            "MAHABHARATHA_BRANCH",
            "MAHABHARATHA_TASK_GRAPH",
            "MAHABHARATHA_SPEC_DIR",
            "MAHABHARATHA_STATE_DIR",
            "MAHABHARATHA_LOG_DIR",
            "MAHABHARATHA_PORT",
        )
    }
    if capability_vars:
        print(f"Worker {args.worker_id} capabilities:", file=sys.stderr)
        for k, v in sorted(capability_vars.items()):
            print(f"  {k}={v}", file=sys.stderr)

    if args.dry_run:
        print(f"Worker {args.worker_id} validated successfully")
        print(f"  Feature: {args.feature}")
        print(f"  Worktree: {args.worktree}")
        print(f"  Branch: {env.get('MAHABHARATHA_BRANCH', 'unknown')}")
        return 0

    # Import and run worker protocol
    # Deferred import to allow dry-run without full dependencies
    try:
        from mahabharatha.protocol_state import WorkerProtocol

        # Resolve task graph path: explicit arg > env > auto-detect from spec dir
        task_graph_path = args.task_graph
        if not task_graph_path:
            env_tg = os.environ.get("MAHABHARATHA_TASK_GRAPH")
            if env_tg:
                task_graph_path = Path(env_tg)
            else:
                spec_dir = os.environ.get("MAHABHARATHA_SPEC_DIR")
                if spec_dir:
                    candidate = Path(spec_dir) / "task-graph.json"
                    if candidate.exists():
                        task_graph_path = candidate

        protocol = WorkerProtocol(
            worker_id=args.worker_id,
            feature=args.feature,
            task_graph_path=task_graph_path,
        )
        protocol.start()
        return 0

    except KeyboardInterrupt:
        print(f"\nWorker {args.worker_id} interrupted")
        return 130  # Standard SIGINT exit code

    except Exception as e:  # noqa: BLE001 — intentional: worker entry-point catch-all; logs and exits with error code
        print(f"Worker {args.worker_id} failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
