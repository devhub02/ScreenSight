"""Watch mode: poll the screen at an interval, only surface frames that changed.

The daemon is a separate OS process (not a thread inside the MCP server) so it
can outlive a per-session MCP connection. It writes a pidfile and a status JSON
file under ~/.screensight/ so the CLI and MCP tools can start/stop/poll it.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

from . import config, core, diff, state

DEFAULT_INTERVAL = config.DEFAULT_WATCH_INTERVAL
DEFAULT_MAX_FRAMES = config.MAX_FRAMES_PER_WATCH


def _write_status(status: dict) -> None:
    config.ensure_base_dir()
    config.DAEMON_STATUS_FILE.write_text(json.dumps(status, indent=2))


def _read_status() -> dict:
    if not config.DAEMON_STATUS_FILE.exists():
        return {"status": "stopped"}
    try:
        return json.loads(config.DAEMON_STATUS_FILE.read_text())
    except Exception:
        return {"status": "stopped"}


def _write_pidfile(pid: int) -> None:
    config.ensure_base_dir()
    config.DAEMON_PID_FILE.write_text(str(pid))


def _read_pidfile() -> int | None:
    if not config.DAEMON_PID_FILE.exists():
        return None
    try:
        return int(config.DAEMON_PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None


def _cleanup_pidfile() -> None:
    config.DAEMON_PID_FILE.unlink(missing_ok=True)


def _cleanup_status() -> None:
    config.DAEMON_STATUS_FILE.unlink(missing_ok=True)


def _daemon_loop(interval: int, max_frames: int) -> None:
    """Internal loop run inside the spawned subprocess. Not called directly."""
    previous_hash: str | None = None
    frames_analyzed = 0
    last_change_ts: float | None = None

    _write_status({
        "status": "running",
        "pid": os.getpid(),
        "interval": interval,
        "max_frames": max_frames,
        "frames_analyzed": 0,
        "last_change_ts": None,
    })

    try:
        while frames_analyzed < max_frames:
            if not state.is_on():
                break

            outcome = core.capture_once()
            if not outcome.ok:
                if outcome.error == "off":
                    break
                time.sleep(interval)
                continue

            if outcome.sha256:
                changed = diff.frame_changed(outcome.sha256, previous_hash)
                if changed:
                    frames_analyzed += 1
                    last_change_ts = time.time()
                    previous_hash = outcome.sha256
                    _write_status({
                        "status": "running",
                        "pid": os.getpid(),
                        "interval": interval,
                        "max_frames": max_frames,
                        "frames_analyzed": frames_analyzed,
                        "last_change_ts": last_change_ts,
                        "last_hash": previous_hash,
                    })

            time.sleep(interval)
    finally:
        if config.AUTO_OFF_ON_WATCH_END:
            state.turn_off()
        _write_status({
            "status": "stopped",
            "frames_analyzed": frames_analyzed,
            "last_change_ts": last_change_ts,
            "last_hash": previous_hash,
        })
        _cleanup_pidfile()


def start_daemon(interval: int = DEFAULT_INTERVAL, max_frames: int = DEFAULT_MAX_FRAMES) -> dict:
    """Spawn a detached subprocess running the watch loop. Returns daemon status."""
    existing = _read_pidfile()
    if existing is not None:
        try:
            os.kill(existing, 0)
            return {"error": f"daemon already running (pid {existing})"}
        except OSError:
            _cleanup_pidfile()

    config.ensure_base_dir()
    proc = subprocess.Popen(
        [sys.executable, "-m", "screensight.watch", str(interval), str(max_frames)],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _write_pidfile(proc.pid)
    return {
        "status": "started",
        "pid": proc.pid,
        "interval": interval,
        "max_frames": max_frames,
    }


def stop_daemon() -> dict:
    """Read the pidfile, send SIGTERM, clean up."""
    pid = _read_pidfile()
    if pid is None:
        return {"status": "not_running"}
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    _cleanup_pidfile()
    _cleanup_status()
    return {"status": "stopped", "pid": pid}


def daemon_status() -> dict:
    """Read daemon.json and return the current status."""
    return _read_status()


def run(
    interval: int = DEFAULT_INTERVAL,
    max_frames: int = DEFAULT_MAX_FRAMES,
) -> None:
    """Generator-based watch loop for direct use (e.g. from MCP tools)."""
    _daemon_loop(interval, max_frames)


# Allow running as: python -m screensight.watch <interval> <max_frames>
if __name__ == "__main__":
    import argparse as _argparse

    _p = _argparse.ArgumentParser(description="ScreenSight watch daemon")
    _p.add_argument("interval", type=int, nargs="?", default=DEFAULT_INTERVAL)
    _p.add_argument("max_frames", type=int, nargs="?", default=DEFAULT_MAX_FRAMES)
    _args = _p.parse_args()
    _daemon_loop(_args.interval, _args.max_frames)
