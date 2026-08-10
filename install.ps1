# ScreenSight installer — installs the package and prints MCP config
# snippets for each supported agent.
#
# Usage:
#   .\install.ps1                    # install only
#   .\install.ps1 -WithClaudeSkill   # also copy legacy Claude Code skill
param(
    [switch]$WithClaudeSkill,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: .\install.ps1 [-WithClaudeSkill]"
    Write-Host ""
    Write-Host "Installs ScreenSight and prints MCP config snippets."
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -WithClaudeSkill   Also copy the legacy Claude Code skill"
    Write-Host "                     into ~/.claude/skills/"
    exit 0
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== ScreenSight Installer ==="
Write-Host ""

# ── 1. Install the package ────────────────────────────────────────────

Write-Host "[1/3] Installing screensight..."
if (Get-Command pipx -ErrorAction SilentlyContinue) {
    pipx install $ScriptDir
} elseif (Get-Command pip -ErrorAction SilentlyContinue) {
    pip install $ScriptDir
} else {
    Write-Host "ERROR: Neither pipx nor pip found. Install Python first." -ForegroundColor Red
    exit 1
}
Write-Host "      Done."
Write-Host ""

# ── 2. Print MCP config snippets ─────────────────────────────────────

Write-Host "[2/3] MCP configuration snippets"
Write-Host ""
Write-Host "Add the appropriate block to your agent's config file."
Write-Host ""

$McpSnippet = @'
{
  "mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
'@

Write-Host "── Claude Code (~/.claude.json or project .mcp.json) ──"
Write-Host $McpSnippet
Write-Host ""

Write-Host "── Cursor (~/.cursor/mcp.json) ──"
Write-Host $McpSnippet
Write-Host ""

Write-Host "── Windsurf (~/.codeium/windsurf/mcp_config.json) ──"
Write-Host $McpSnippet
Write-Host ""

Write-Host "── Cline (VS Code settings, cline.mcpServers) ──"
Write-Host $McpSnippet
Write-Host ""

Write-Host "── Aider / anything without MCP ──"
Write-Host "No config needed — use the CLI directly:"
Write-Host "  screensight capture   # prints frame path to stdout"
Write-Host ""

# ── 3. Optional: Claude Code skill ────────────────────────────────────

Write-Host "[3/3] Claude Code skill..."
if ($WithClaudeSkill) {
    $SkillDir = Join-Path $env:USERPROFILE ".claude\skills"
    New-Item -ItemType Directory -Force -Path $SkillDir | Out-Null
    Copy-Item (Join-Path $ScriptDir "skills\claude-code\SKILL.md") (Join-Path $SkillDir "SKILL.md") -Force
    Write-Host "      Copied to $SkillDir\SKILL.md"
} else {
    Write-Host "      Skipped (use -WithClaudeSkill to install)"
}
Write-Host ""

Write-Host "=== Installation complete ==="
Write-Host "Run 'screensight --help' to get started."
