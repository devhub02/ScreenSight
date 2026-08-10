# ScreenSight

**One line:** Let *any* coding agent see your screen — not just Claude Code. MCP server + CLI fallback + a standalone watch daemon. No API key; runs on whatever subscription/session the agent already has.

## Why this exists

Coding agents that can see your screen give far better debugging advice — but most solutions are locked to a single agent. Every other agent — Cursor, Windsurf, Cline, Codex CLI, Aider — either reinvents this or does without.

ScreenSight generalizes it:
- Ships as an **MCP server** → works in any MCP-capable agent (Cursor, Windsurf, Cline, Claude Code, Codex CLI) with zero agent-specific code.
- Ships a **CLI** → works for agents with no MCP support (Aider, raw shell agents) by shelling out.
- Ships a **watch daemon** → a long-lived background process that owns the interval/diffing logic once, so both the MCP tools and the CLI just read its output instead of re-implementing polling.

## Non-negotiables (carried over + strengthened from the original)

1. **Off by default.** A master switch (`~/.screensight/state.json`) gates every capture. The check happens inside the capture pipeline itself (`core.py::capture_once`), not in a prompt or tool description — so no instruction, injected or otherwise, can talk the tool into capturing while it's off.
2. **Sensitive-app blocklist.** Before a frame is written, the active window/app title is checked against a blocklist (password managers, private/incognito windows). Matches abort the capture — nothing is saved, nothing is sent. User-extensible via `~/.screensight/redact_zones.json`.
3. **Zone redaction.** User can define fixed screen rectangles that always get blacked out (e.g. "top-left corner where my banking app lives").
4. **Frame hygiene.** One frame file, overwritten each capture, deleted on `off`. Never accumulate a folder of screenshots.
5. **Watch mode self-limits.** Max 10 analyzed frames per invocation (context/token cost), auto-turns-off when a watch session ends so an idle daemon can't quietly keep running.
6. **Downscale to 1568px long edge** before anything leaves disk — the point past which more pixels don't help a vision model, and it keeps every consumer's token cost down.

## What's already built (do not redo — extend)

```
src/screensight/
  config.py        # paths, constants, blocklist defaults, redact-config loader
  state.py         # master on/off switch (is_on/turn_on/turn_off/status)
  capture/
    base.py        # CaptureBackend ABC + get_backend() OS dispatch
    macos.py        # screencapture + osascript for active window title
    linux.py         # grim / gnome-screenshot / import, xdotool for title
    windows.py        # PowerShell + System.Drawing, WSLCapture subclass for WSL
  privacy.py       # title_is_blocked(), process_frame() (downscale + zone redact)
  diff.py          # sha256_of_file(), frame_changed()
  core.py          # capture_once() — THE single entrypoint every surface calls
```

`core.capture_once()` is the seam: it checks the switch, calls the platform backend, checks the blocklist, redacts/downscales, hashes. CLI, MCP tools, and the daemon must all call this — never call a platform `capture/*.py` module directly.

## What's left to build

See `TASKS.md` for the ordered checklist. In short:

1. `watch.py` — the daemon: loop on an interval, call `core.capture_once()`, skip unchanged frames via `diff.frame_changed()`, write `~/.screensight/daemon.json` (status: running, frames_analyzed, last_change_ts, last_hash), respect `MAX_FRAMES_PER_WATCH`, auto-call `state.turn_off()` when it stops.
2. `mcp_server.py` — FastMCP server exposing tools: `screen_enable`, `screen_disable`, `screen_status`, `screen_capture(question?, display?)`, `screen_watch_start(interval?, max_frames?)`, `screen_watch_stop`, `screen_watch_latest`, `screen_list_displays`. `screen_capture` returns an MCP Image content block read from the path `core.capture_once()` wrote.
3. `__main__.py` — CLI (argparse, no extra deps) mirroring the same verbs: `screensight on|off|status|capture|watch [--interval N]|watch-stop|displays`.
4. `install.sh` / `install.ps1` — `pip install .`, print the MCP registration snippet for each target agent's config file (see below), offer to also drop the legacy Claude Code skill adapter into `~/.claude/skills/` for backward compat.
5. `skills/claude-code/SKILL.md` — thin adapter: same `/claude-screen`-style commands, but shells out to the installed `screensight` CLI instead of bundling its own capture scripts. Kept for people already on the original skill.
6. `README.md` — install + per-agent config snippets + comparison table vs the original.
7. `tests/` — at minimum: state on/off round-trip, blocklist matching, diff hashing, redact-zone scaling math. Mock subprocess calls for capture backends; do not screenshot in CI.

## Per-agent integration (MCP config snippets — put these in README.md)

- **Claude Code** (`~/.claude.json` or project `.mcp.json`): standard `mcpServers` block, command `screensight-mcp`.
- **Cursor** (`~/.cursor/mcp.json`): same shape.
- **Windsurf** (`~/.codeium/windsurf/mcp_config.json`): same shape.
- **Cline** (VS Code settings under `cline.mcpServers`): same shape.
- **Aider / anything without MCP**: no config needed — the CLI works standalone: `screensight capture` prints the frame path, agent reads it as a normal file/image argument.

## Explicitly out of scope for v1

- OCR-based auto-detection of sensitive content (blocklist + manual zones cover it for now; revisit post-v1).
- Region-of-interest *capture* (only full-screen for now; redaction zones are a separate, already-built concept).
- A GUI settings app. Config is a JSON file, edited by hand or by the agent itself.
