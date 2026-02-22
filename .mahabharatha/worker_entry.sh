#!/bin/bash
# MAHABHARATHA Worker Entry - Invokes worker_main to execute assigned tasks
set -e

WORKER_ID=${MAHABHARATHA_WORKER_ID:-0}
FEATURE=${MAHABHARATHA_FEATURE}
WORKTREE=${MAHABHARATHA_WORKTREE:-/workspace}
BRANCH=${MAHABHARATHA_BRANCH}
SPEC_DIR=${MAHABHARATHA_SPEC_DIR}

echo "========================================"
echo "MAHABHARATHA Worker $WORKER_ID starting..."
echo "Feature: $FEATURE"
echo "Worktree: $WORKTREE"
echo "Branch: $BRANCH"
echo "Spec Dir: $SPEC_DIR"
echo "========================================"

cd "$WORKTREE"

# Fix git worktree paths for container environment
# The worktree metadata is mounted from the host but uses host-specific paths.
# We create a local copy of the metadata and fix paths without modifying the mounted original.
if [ -n "$MAHABHARATHA_GIT_WORKTREE_DIR" ] && [ -d "$MAHABHARATHA_GIT_WORKTREE_DIR" ]; then
    echo "Setting up git worktree for container..."
    LOCAL_GIT_DIR="$WORKTREE/.git-local"

    # Create a local copy of worktree metadata
    rm -rf "$LOCAL_GIT_DIR"
    cp -r "$MAHABHARATHA_GIT_WORKTREE_DIR" "$LOCAL_GIT_DIR"

    # Point worktree's .git to local copy
    echo "gitdir: $LOCAL_GIT_DIR" > "$WORKTREE/.git"

    # Fix gitdir in local copy to point to this worktree
    echo "$WORKTREE/.git" > "$LOCAL_GIT_DIR/gitdir"

    # Fix commondir to point to mounted main repo's .git
    if [ -n "$MAHABHARATHA_GIT_MAIN_DIR" ]; then
        echo "$MAHABHARATHA_GIT_MAIN_DIR" > "$LOCAL_GIT_DIR/commondir"
    fi

    echo "Git worktree configured: LOCAL_GIT_DIR=$LOCAL_GIT_DIR"

    # Configure git user identity for commits
    git config user.email "mahabharatha-worker@local"
    git config user.name "MAHABHARATHA Worker $WORKER_ID"
fi

# Create healthcheck marker file (checked by Dockerfile HEALTHCHECK)
touch /tmp/.mahabharatha-alive

# Remove marker on exit to signal unhealthy state
cleanup() {
    rm -f /tmp/.mahabharatha-alive
}
trap cleanup EXIT

# Ensure 'python' is available (some containers only have python3)
if ! command -v python &>/dev/null && command -v python3 &>/dev/null; then
    # Try system path first, fall back to user-writable location
    ln -sf "$(command -v python3)" /usr/local/bin/python 2>/dev/null || \
    ln -sf "$(command -v python3)" "$HOME/.local/bin/python" 2>/dev/null || \
    { mkdir -p /tmp/bin && ln -sf "$(command -v python3)" /tmp/bin/python && export PATH="/tmp/bin:$PATH"; }
fi

# Install MAHABHARATHA dependencies if not already installed
if ! python3 -c "import pydantic" 2>/dev/null || ! python3 -c "import pytest" 2>/dev/null; then
    echo "Installing MAHABHARATHA dependencies..."
    pip3 install -q --break-system-packages -e ".[dev]" 2>/dev/null || \
        pip3 install -q --break-system-packages pydantic click rich jsonschema pytest
fi

# Ensure pip-installed scripts are in PATH (pytest, ruff, mypy, etc.)
USER_BIN="$(python3 -m site --user-base 2>/dev/null)/bin"
[ -d "$USER_BIN" ] && export PATH="$USER_BIN:$PATH"
export PATH="/usr/local/bin:$HOME/.local/bin:$PATH"

# Run the MAHABHARATHA worker main
# Note: Do NOT use 'exec' here -- the container CMD has a fallback sleep
# after this script to keep the container alive for debugging if worker exits.
python3 -m mahabharatha.worker_main \
     --worker-id "$WORKER_ID" \
     --feature "$FEATURE" \
     --worktree "$WORKTREE" \
     --branch "$BRANCH" \
     --verbose
EXIT_CODE=$?
echo "Worker $WORKER_ID exited with code $EXIT_CODE"
exit $EXIT_CODE
