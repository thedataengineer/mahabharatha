#!/bin/bash
# MAHABHARATHA Installation Script
# Copies MAHABHARATHA files to the current project

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-.}"

echo "Installing MAHABHARATHA to $TARGET_DIR..."

# Create directories
mkdir -p "$TARGET_DIR/.mahabharatha"
mkdir -p "$TARGET_DIR/.claude/commands/mahabharatha"
mkdir -p "$TARGET_DIR/.claude/commands/z"
mkdir -p "$TARGET_DIR/.devcontainer/mcp-servers"
mkdir -p "$TARGET_DIR/.gsd/specs"

# Copy orchestrator and config
cp "$SCRIPT_DIR/.mahabharatha/orchestrator.py" "$TARGET_DIR/.mahabharatha/"
cp "$SCRIPT_DIR/.mahabharatha/config.yaml" "$TARGET_DIR/.mahabharatha/"

# Copy slash commands into mahabharatha/ and z/ subdirs
cp "$SCRIPT_DIR/.claude/commands/mahabharatha/"*.md "$TARGET_DIR/.claude/commands/mahabharatha/"
cp "$SCRIPT_DIR/.claude/commands/z/"*.md "$TARGET_DIR/.claude/commands/z/"

# Copy devcontainer files
cp "$SCRIPT_DIR/.devcontainer/devcontainer.json" "$TARGET_DIR/.devcontainer/"
cp "$SCRIPT_DIR/.devcontainer/Dockerfile" "$TARGET_DIR/.devcontainer/"
cp "$SCRIPT_DIR/.devcontainer/docker-compose.yaml" "$TARGET_DIR/.devcontainer/"
cp "$SCRIPT_DIR/.devcontainer/post-create.sh" "$TARGET_DIR/.devcontainer/"
cp "$SCRIPT_DIR/.devcontainer/post-start.sh" "$TARGET_DIR/.devcontainer/"
cp "$SCRIPT_DIR/.devcontainer/mcp-servers/config.json" "$TARGET_DIR/.devcontainer/mcp-servers/"

# Make scripts executable
chmod +x "$TARGET_DIR/.mahabharatha/orchestrator.py"
chmod +x "$TARGET_DIR/.devcontainer/post-create.sh"
chmod +x "$TARGET_DIR/.devcontainer/post-start.sh"

echo ""
echo "MAHABHARATHA installed successfully!"
echo ""
echo "Next steps:"
echo "  1. cd $TARGET_DIR"
echo "  2. claude"
echo "  3. /init"
echo ""
echo "Commands available:"
echo "  /init     - Initialize project infrastructure"
echo "  /plan     - Plan a feature"
echo "  /design   - Design architecture and task graph"
echo "  /kurukshetra     - Launch parallel workers"
echo "  /status   - Check progress"
echo ""
