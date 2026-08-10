# ScreenSight — Claude Code Skill (Compatibility Shim)

> **Note:** This is a legacy compatibility shim for users of the original
> ScreenSight skill. The primary integration path is now the MCP server —
> see the main README for setup instructions. This skill shells out to the
> installed `screensight` CLI for backward compatibility.

## Commands

### /claude-screen-on
Turn on screen capture access.

```
screensight on
```

### /claude-screen-off
Turn off screen capture access.

```
screensight off
```

### /claude-screen-status
Check whether screen access is on or off.

```
screensight status
```

### /claude-screen-capture
Capture the current screen and return the image path.

```
screensight capture
```

### /claude-screen-watch [interval] [max-frames]
Start a bounded watch session. Default: interval=5s, max-frames=10.

```
screensight watch --interval ${1:-5} --max-frames ${2:-10}
```

### /claude-screen-watch-stop
Stop the running watch daemon.

```
screensight watch-stop
```

### /claude-screen-watch-status
Check the watch daemon status.

```
screensight watch-status
```

### /claude-screen-displays
List available displays/monitors.

```
screensight displays
```

## Usage

These commands are meant to be run in a shell. In Claude Code, you can
use them by asking the agent to run the corresponding `screensight` CLI
command, or by setting up the MCP server (recommended) for automatic
tool access.

## Privacy

- Screen capture is **off by default** — you must explicitly enable it.
- Sensitive apps (password managers, private browsing) are auto-blocked.
- The master switch is enforced in code, not just in prompts.
