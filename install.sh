#!/usr/bin/env bash
# ScreenSight installer — installs the package and prints MCP config
# snippets for each supported agent.
#
# Usage:
#   bash install.sh                 # install only
#   bash install.sh --with-claude-skill   # also copy legacy Claude Code skill
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WITH_CLAUDE_SKILL=false

for arg in "$@"; do
    case "$arg" in
        --with-claude-skill) WITH_CLAUDE_SKILL=true ;;
        -h|--help)
            echo "Usage: bash install.sh [--with-claude-skill]"
            echo ""
            echo "Installs ScreenSight and prints MCP config snippets."
            echo ""
            echo "Options:"
            echo "  --with-claude-skill   Also copy the legacy Claude Code skill"
            echo "                       into ~/.claude/skills/"
            exit 0
            ;;
    esac
done

echo "=== ScreenSight Installer ==="
echo ""

# ── 1. Install the package ────────────────────────────────────────────

echo "[1/3] Installing screensight..."
if command -v pipx &>/dev/null; then
    pipx install "$SCRIPT_DIR"
elif command -v pip &>/dev/null; then
    pip install "$SCRIPT_DIR"
else
    echo "ERROR: Neither pipx nor pip found. Install Python first." >&2
    exit 1
fi
echo "      Done."
echo ""

# ── 2. Print MCP config snippets ─────────────────────────────────────

echo "[2/3] MCP configuration snippets"
echo ""
echo "Add the appropriate block to your agent's config file."
echo ""

MCP_SNIPPET='{
  "mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}'

echo "── Claude Code (~/.claude.json or project .mcp.json) ──"
echo "$MCP_SNIPPET"
echo ""

echo "── Cursor (~/.cursor/mcp.json) ──"
echo "$MCP_SNIPPET"
echo ""

echo "── Windsurf (~/.codeium/windsurf/mcp_config.json) ──"
echo "$MCP_SNIPPET"
echo ""

echo "── Cline (VS Code settings, cline.mcpServers) ──"
echo "$MCP_SNIPPET"
echo ""

echo "── Aider / anything without MCP ──"
echo "No config needed — use the CLI directly:"
echo "  screensight capture   # prints frame path to stdout"
echo ""

# ── 3. Optional: Claude Code skill ────────────────────────────────────

echo "[3/3] Claude Code skill..."
if [ "$WITH_CLAUDE_SKILL" = true ]; then
    SKILL_DIR="$HOME/.claude/skills"
    mkdir -p "$SKILL_DIR"
    cp "$SCRIPT_DIR/skills/claude-code/SKILL.md" "$SKILL_DIR/SKILL.md"
    echo "      Copied to $SKILL_DIR/SKILL.md"
else
    echo "      Skipped (use --with-claude-skill to install)"
fi
echo ""

echo "=== Installation complete ==="
echo "Run 'screensight --help' to get started."
