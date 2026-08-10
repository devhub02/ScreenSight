# ScreenSight User Guide

A step-by-step guide to giving your coding agent screen vision.

## Quick Start (2 minutes)

```bash
# 1. Install
git clone <repo-url> screensight
cd screensight
pip install .

# 2. Enable capture
screensight on

# 3. Take a screenshot
screensight capture

# 4. Check status
screensight status

# 5. Turn off
screensight off
```

That's it. Your agent can now see your screen.

## Table of Contents

- [Installation](#installation)
- [Setup by Agent](#setup-by-agent)
  - [Claude Code](#claude-code)
  - [Cursor](#cursor)
  - [Windsurf](#windsurf)
  - [Cline](#cline)
  - [Aider (no MCP)](#aider-no-mcp)
- [CLI Reference](#cli-reference)
- [MCP Tools Reference](#mcp-tools-reference)
- [Watch Mode](#watch-mode)
- [Privacy & Security](#privacy--security)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Installation

### Option 1: From source (recommended)

```bash
git clone <repo-url> screensight
cd screensight
pip install .
```

### Option 2: Using the installer script

```bash
# Linux / macOS
bash install.sh

# Windows
.\install.ps1
```

The installer also prints MCP config snippets for your agent.

### Option 3: Using pipx (isolated install)

```bash
pipx install .
```

### Verify installation

```bash
screensight --help
screensight-mcp --help
```

---

## Setup by Agent

### Claude Code

**Option A: Project-level config (recommended)**

Create `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
```

**Option B: Global config**

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
```

**Option C: Legacy skill adapter**

```bash
bash install.sh --with-claude-skill
```

This copies the legacy skill to `~/.claude/skills/SKILL.md`.

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
```

Restart Cursor after adding the config.

### Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
```

Restart Windsurf after adding the config.

### Cline

Add to VS Code settings (`settings.json`):

```json
{
  "cline.mcpServers": {
    "screensight": {
      "command": "screensight-mcp"
    }
  }
}
```

Restart VS Code after adding the config.

### Aider (no MCP)

No config needed. Aider can use the CLI directly.

In your agent instructions or system prompt, add:

```
When I ask you to look at my screen, run:
  screensight capture

The output will contain a "path" field with the screenshot location.
Read that file to see what's on my screen.
```

---

## CLI Reference

### Basic commands

| Command | What it does |
|---------|--------------|
| `screensight on` | Enable screen capture |
| `screensight off` | Disable capture + delete frame |
| `screensight status` | Show if capture is enabled |

### Capture

```bash
# Capture primary display
screensight capture

# Capture specific display
screensight capture --display 1
```

Output (JSON):

```json
{
  "path": "C:\\Users\\you\\.screensight\\frame.jpg",
  "sha256": "3d950ca5b883...",
  "active_window_title": "main.py - VS Code"
}
```

### List displays

```bash
screensight displays
```

Output:

```
Available displays:
  Display 0: primary (1920x1080)
  Display 1: secondary (2560x1440)
```

### Watch mode

```bash
# Start watching (default: every 5s, max 10 frames)
screensight watch

# Custom interval and max frames
screensight watch --interval 3 --max-frames 20

# Check what the daemon is doing
screensight watch-status

# Stop watching
screensight watch-stop
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `3` | Switch is off, or capture failed |

---

## MCP Tools Reference

When using ScreenSight via MCP, these 8 tools are available to your agent:

### screen_enable

Turn on the master switch. Must be called before any capture.

```
Tool: screen_enable
Input: none
Output: "ScreenSight enabled. State: {'enabled': True, ...}"
```

### screen_disable

Turn off the master switch. Stops any running watch daemon.

```
Tool: screen_disable
Input: none
Output: "ScreenSight disabled. State: {'enabled': False, ...}"
```

### screen_status

Check if the master switch is on or off.

```
Tool: screen_status
Input: none
Output: "ScreenSight is ON. Details: {'enabled': True, ...}"
```

### screen_capture

Capture the screen and return the image.

```
Tool: screen_capture
Input:
  - question (optional): Text to echo back for context
  - display (optional): Display index (omit for primary)
Output: Image content block + text with window title, path, hash
```

Example: Ask the agent "what's on my screen?" and it will call `screen_capture`, receive the image, and describe what it sees.

### screen_watch_start

Start a background daemon that captures on an interval.

```
Tool: screen_watch_start
Input:
  - interval (default 5): Seconds between captures
  - max_frames (default 10): Max changed frames before auto-stop
Output: "Watch daemon started: {'running': True, 'pid': 12345, ...}"
```

### screen_watch_stop

Stop the running daemon.

```
Tool: screen_watch_stop
Input: none
Output: "Watch daemon stopped: {'running': False, ...}"
```

### screen_watch_latest

Check daemon progress.

```
Tool: screen_watch_latest
Input: none
Output:
  Daemon running: True
  Status: running
  Frames analyzed: 3
  Last hash: 15dc34902d50...
  Interval: 5s
  Max frames: 10
```

### screen_list_displays

List available monitors.

```
Tool: screen_list_displays
Input: none
Output:
  Available displays:
    Display 0: primary (1920x1080)
    Display 1: secondary (2560x1440)
```

---

## Watch Mode

Watch mode is a background daemon that captures your screen at regular intervals. It's useful for:

- Monitoring changes over time
- Letting your agent observe a process
- Debugging issues that happen intermittently

### How it works

1. `screensight watch` spawns a detached background process
2. The daemon calls `capture_once()` every N seconds
3. Unchanged frames are skipped (hash comparison)
4. After `max_frames` changed frames, it auto-stops
5. The master switch is turned off when it exits

### Example workflow

```bash
# Start watching every 3 seconds, max 15 frames
screensight watch --interval 3 --max-frames 15

# Do your work...

# Check progress
screensight watch-status
# {"frames_analyzed": 5, "status": "running", ...}

# Stop early if needed
screensight watch-stop

# Or let it run — it stops itself after 15 changed frames
```

### Files created

| File | Purpose |
|------|---------|
| `~/.screensight/frame.jpg` | Latest captured frame |
| `~/.screensight/daemon.json` | Daemon status and stats |
| `~/.screensight/daemon.pid` | Daemon process ID |

---

## Privacy & Security

ScreenSight is built with privacy as a core requirement, not an afterthought.

### Master switch

- **Default: OFF** — nothing happens until you explicitly enable it
- Check is in `core.capture_once()` — can't be bypassed by prompt injection
- `screensight off` turns it off AND deletes the frame

### Blocklist

Sensitive apps are auto-blocked. If the active window title matches, capture is refused:

- Password managers (1Password, Bitwarden, KeePass, LastPass)
- Private browsing windows
- Keychain Access
- Any window with "password" in the title

Customize in `~/.screensight/redact_zones.json`:

```json
{
  "blocklist": ["1password", "bitwarden", "my-banking-app"],
  "zones": []
}
```

### Zone redaction

Black out specific screen areas before saving:

```json
{
  "zones": [
    {"x": 0, "y": 0, "w": 200, "h": 100, "label": "notification area"},
    {"x": 1700, "y": 0, "w": 220, "h": 40, "label": "system tray"}
  ]
}
```

### Frame hygiene

- One file, overwritten each time
- Deleted on `screensight off`
- Never accumulates a folder of screenshots

### Downscaling

Images are resized to 1568px long edge — past the point where more pixels help a vision model. This keeps token costs low.

---

## Configuration

All config lives in `~/.screensight/`:

```
~/.screensight/
  state.json          # Master on/off switch
  frame.jpg           # Latest captured frame
  daemon.json         # Watch daemon status
  daemon.pid          # Watch daemon process ID
  redact_zones.json   # Blocklist + redaction zones
  screensight.log     # Log file (if enabled)
```

### redact_zones.json

```json
{
  "blocklist": [
    "1password",
    "bitwarden",
    "keychain access",
    "keepass",
    "lastpass",
    "password",
    "private browsing",
    "incognito"
  ],
  "zones": [
    {"x": 0, "y": 0, "w": 200, "h": 100, "label": "optional label"}
  ]
}
```

---

## Troubleshooting

### "Capture failed: off"

The master switch is off. Run:

```bash
screensight on
screensight capture
```

### "blocked: active window '...' matches the sensitive-app blocklist"

Your current window title contains a blocklist word. Either:
1. Switch to a different window and try again
2. Remove the word from your blocklist in `~/.screensight/redact_zones.json`

### "PowerShell capture failed" (Windows)

Ensure PowerShell is available and you have permission to take screenshots:

```bash
powershell.exe -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SystemInformation]::VirtualScreen"
```

### "Daemon already running"

A watch daemon is already active. Check its status or stop it:

```bash
screensight watch-status
screensight watch-stop
```

### Frame file doesn't exist after capture

The capture may have failed silently. Check:

```bash
screensight status
screensight capture 2>&1
```

### MCP server not starting

Verify the command is correct:

```bash
which screensight-mcp    # Linux/macOS
where screensight-mcp    # Windows
```

If not found, reinstall:

```bash
pip install -e .
```

---

## Getting Help

- Run `screensight --help` for CLI options
- Check `screensight status` to see the current state
- Look at `~/.screensight/screensight.log` for errors
- Open an issue on GitHub
