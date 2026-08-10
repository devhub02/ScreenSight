# ARCHITECTURE.md

## Data flow

```mermaid
flowchart TD
    subgraph state["state.py — Master On/Off Switch"]
        stateFile["~/.screensight/state.json"]
    end

    subgraph inputs["Input Surfaces"]
        CLI["CLI (__main__.py)"]
        MCP["MCP Server (mcp_server.py)"]
        WatchDaemon["Watch Daemon (watch.py)"]
    end

    subgraph core["core.py — capture_once()"]
        capture["capture_once()"]
    end

    subgraph capture_backends["capture/ — Platform Backends"]
        base["base.py (CaptureBackend)"]
        macos["macos.py"]
        linux["linux.py"]
        windows["windows.py"]
    end

    subgraph privacy["privacy.py"]
        blocklist["Title Blocklist Check"]
        downscale["Downscale"]
        redact["Zone Redact"]
    end

    subgraph diff["diff.py"]
        hash["SHA-256 Hash"]
        change["Change Detection"]
    end

    stateFile -->|"is_on()?"| CLI
    stateFile -->|"is_on()?"| MCP
    stateFile -->|"is_on()?"| WatchDaemon

    CLI --> capture
    MCP --> capture
    WatchDaemon --> capture

    capture --> base
    base --> macos
    base --> linux
    base --> windows

    capture --> blocklist
    blocklist -->|"abort if blocked"| BLOCKED["❌ Blocked"]
    blocklist --> downscale
    downscale --> redact

    redact --> hash
    hash --> change
    change -->|"new frame"| WRITE["Write frame.jpg"]
    change -->|"same as last"| SKIP["Skip"]
```

## Three surfaces, one core

- **CLI** (`__main__.py`) — synchronous, human- or shell-script-facing. Talks to `core.py` and `watch.py` directly, formats results as text.
- **MCP server** (`mcp_server.py`) — agent-facing. Same calls as the CLI, wrapped as FastMCP tools with agent-readable docstrings. Returns MCP `Image` content blocks, not file paths, so the calling agent can look at the frame directly in its own context.
- **Watch daemon** (`watch.py`, run as a detached OS process) — the only surface that runs unattended. Owns the interval loop; CLI and MCP server both just start/stop/poll it rather than each implementing their own loop. This is why the daemon exists as a separate process instead of a background thread inside the MCP server: the MCP server's process lifetime is tied to the agent session (often stdio, often per-request), which is the wrong lifetime for "check my screen every 5 seconds."

## Why `core.capture_once()` is the choke point

Every safety property in `PROJECT.md` (switch check, blocklist, redaction, downscale, hashing) is composed once, in order, inside `capture_once()`. Any new surface — a future web UI, a future gRPC endpoint, whatever — gets all of them for free by calling that one function. The moment a second code path calls a `capture/*.py` backend directly, the safety properties can silently diverge between surfaces. Treat that as a bug, not a style preference.

## State files (all under `~/.screensight/`)

| File | Written by | Read by | Purpose |
|---|---|---|---|
| `state.json` | `state.py` | `core.py` | master on/off switch |
| `frame.jpg` | `core.py` (via `privacy.process_frame`) | CLI, MCP tools | the one current screenshot, overwritten each capture |
| `redact_zones.json` | user (hand-edited or agent-edited) | `privacy.py` | blocklist terms + redaction rectangles |
| `daemon.json` | `watch.py` daemon loop | CLI `status`, MCP `screen_watch_latest` | running/stopped, frame count, last change timestamp |
| `daemon.pid` | `watch.py` (on start) | `watch.py` (on stop) | so `watch-stop` can find the process |

## Platform backend contract

Every `capture/*.py` module implements `CaptureBackend`:

- `screenshot(out_path, display=None) -> CaptureResult` — must be a native OS tool call via `subprocess`, never a Python screenshot library (keeps the "no extra app, no extra deps" property).
- `active_window_title() -> str | None` — best-effort; `None` means "couldn't determine," and every caller must treat that as **not verified safe**, not as "safe."
- `list_displays() -> list[dict]` — at minimum `[{"index": 0, "name": "primary"}]` as a fallback.
