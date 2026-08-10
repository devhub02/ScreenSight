"""MCP server exposing screen access as tools.

Any MCP-compatible agent (Claude Code, Cursor, Windsurf, Cline, Codex CLI)
can attach to this over stdio and get the same tools — this is the actual
"works for any coding agent" part, since MCP is the one interface all of
them converge on.
"""
from __future__ import annotations

from fastmcp import FastMCP

from . import core, state, watch

mcp = FastMCP(
    name="screensight",
    instructions=(
        "Gives you the ability to see the user's screen. Screen access is OFF "
        "by default and gated by an explicit switch — call screen_enable before "
        "any capture tool, and call screen_disable as soon as you're done, "
        "especially before the user might show you something private. Frames are "
        "automatically downscaled and scrubbed for redaction zones, but that is "
        "a backup, not a substitute for turning access off when you're finished."
    ),
)


@mcp.tool()
def screen_enable() -> dict:
    """Enable screen capture access. Required before any other screen_* tool.
    The switch stays on until you call screen_disable."""
    state.turn_on()
    return state.status()


@mcp.tool()
def screen_disable() -> dict:
    """Disable screen capture access immediately and delete any cached frame."""
    state.turn_off()
    return state.status()


@mcp.tool()
def screen_status() -> dict:
    """Check whether screen access is currently on, and what displays are available."""
    return {
        **state.status(),
        "displays": core.list_displays(),
    }


@mcp.tool()
def screen_capture(question: str = "", display: int | None = None) -> str:
    """Capture the current screen and return it as an image for you to look at.

    display=None captures the primary display; pass a specific display index
    from screen_status to capture just one. The active window title is included
    so you know what was visible. If question is given, it is echoed back so
    your own reasoning addresses it — the tool does not call another model.

    Returns the file path of the captured frame (a JPEG at ~/.screensight/frame.jpg)."""
    outcome = core.capture_once(display=display)
    if not outcome.ok:
        return f"Capture failed: {outcome.error}"

    result = f"Captured: {outcome.path}"
    if outcome.active_window_title:
        result += f"\nActive window: {outcome.active_window_title}"
    if question:
        result += f"\nQuestion: {question}"
    return result


@mcp.tool()
def screen_watch_start(interval: int = 5, max_frames: int = 10) -> dict:
    """Start a bounded watch session: polls the screen every interval seconds,
    captures frames that changed, up to max_frames changed frames, then stops
    and turns screen access off automatically. Call this instead of looping
    screen_capture yourself — it has the unchanged-frame skip and the hard cap
    built in so an idle screen costs nothing and a forgotten session can't run
    forever."""
    return watch.start_daemon(interval=interval, max_frames=max_frames)


@mcp.tool()
def screen_watch_stop() -> dict:
    """Stop a running watch daemon immediately."""
    return watch.stop_daemon()


@mcp.tool()
def screen_watch_status() -> dict:
    """Check the status of a running or recently finished watch daemon."""
    return watch.daemon_status()


@mcp.tool()
def screen_list_displays() -> list[dict]:
    """List all available displays/monitors. Use the display index from this
    list when calling screen_capture to target a specific screen."""
    return core.list_displays()


def run() -> None:
    """Entry point for the screensight-mcp script."""
    mcp.run()


if __name__ == "__main__":
    run()
