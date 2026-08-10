from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .base import CaptureBackend, CaptureResult

_PS_SCRIPT = r"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bmp)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bmp.Save('{out_path}', [System.Drawing.Imaging.ImageFormat]::Jpeg)
$graphics.Dispose(); $bmp.Dispose()

Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public class ActiveWin {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
}
'@
$h = [ActiveWin]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder 256
[void][ActiveWin]::GetWindowText($h, $sb, 256)
Write-Output $sb.ToString()
"""


class WindowsCapture(CaptureBackend):
    def screenshot(self, out_path: str, display: Optional[int] = None) -> CaptureResult:
        script = _PS_SCRIPT.format(out_path=out_path.replace("\\", "\\\\"))
        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", script],
                capture_output=True, text=True, timeout=20,
            )
            if proc.returncode != 0:
                return CaptureResult(ok=False, error=proc.stderr.strip() or "PowerShell capture failed")
            title = proc.stdout.strip() or None
            return CaptureResult(ok=True, path=out_path, active_window_title=title)
        except FileNotFoundError:
            return CaptureResult(ok=False, error="powershell.exe not found")
        except subprocess.TimeoutExpired:
            return CaptureResult(ok=False, error="PowerShell capture timed out")


class WSLCapture(WindowsCapture):
    """From inside WSL, capture the real Windows desktop, then copy the
    result back across the filesystem boundary into WSL's temp dir."""

    def screenshot(self, out_path: str, display: Optional[int] = None) -> CaptureResult:
        win_tmp = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", "$env:TEMP"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        win_out = f"{win_tmp}\\screensight-frame.jpg"
        result = super().screenshot(win_out, display)
        if not result.ok:
            return result

        try:
            wsl_path = subprocess.run(
                ["wslpath", "-u", win_out], capture_output=True, text=True, timeout=5
            ).stdout.strip()
            Path(out_path).write_bytes(Path(wsl_path).read_bytes())
            Path(wsl_path).unlink(missing_ok=True)  # delete from the Windows temp folder immediately
            return CaptureResult(ok=True, path=out_path, active_window_title=result.active_window_title)
        except Exception as e:
            return CaptureResult(ok=False, error=f"WSL copy-back failed: {e}")
