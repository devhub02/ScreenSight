from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class CaptureResult:
    ok: bool
    path: Optional[str] = None
    error: Optional[str] = None
    active_window_title: Optional[str] = None


class CaptureBackend:
    """One method each platform module must implement."""

    def screenshot(self, out_path: str, display: Optional[int] = None) -> CaptureResult:
        raise NotImplementedError

    def active_window_title(self) -> Optional[str]:
        """Best-effort. Return None if the platform has no easy way to get it —
        callers must treat None as 'unknown', not 'safe'."""
        return None

    def list_displays(self) -> list[dict]:
        return [{"index": 0, "name": "primary"}]


def get_backend():
    from ..config import get_os

    os_name = get_os()
    if os_name == "macos":
        from .macos import MacOSCapture
        return MacOSCapture()
    if os_name == "windows":
        from .windows import WindowsCapture
        return WindowsCapture()
    if os_name == "wsl":
        from .windows import WSLCapture
        return WSLCapture()
    from .linux import LinuxCapture
    return LinuxCapture()
