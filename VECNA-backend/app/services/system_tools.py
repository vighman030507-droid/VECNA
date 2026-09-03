"""
Autonomous System & Web Tools for VECNA.
Enables real-time system operations (volume control, lock screen, media control),
and silent DuckDuckGo web research to ground answers with live factual context.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import Any
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


def adjust_system_volume(level: int) -> dict[str, Any]:
    """Adjust system master volume (0-100%). Compatible with macOS and Windows."""
    level = max(0, min(100, level))
    try:
        if sys.platform == "darwin":
            # macOS: 'set volume output volume X' uses 0-100 scale
            subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
            return {"ok": True, "message": f"Volume set to {level}%"}
        elif sys.platform == "win32":
            # Windows: PowerShell script adjusting audio endpoint
            ps_cmd = (
                f"$obj = New-Object -ComObject WScript.Shell; "
                f"1..50 | ForEach-Object {{ $obj.SendKeys([char]174) }}; "
                f"1..{level // 2} | ForEach-Object {{ $obj.SendKeys([char]175) }}"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=False)
            return {"ok": True, "message": f"Volume adjusted to {level}%"}
        return {"ok": False, "error": "Unsupported platform"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def lock_screen() -> dict[str, Any]:
    """Instantly lock host computer screen. Compatible with macOS and Windows."""
    try:
        if sys.platform == "darwin":
            # Modern macOS lock screen command
            res = subprocess.run(["pmset", "displaysleepnow"], check=False)
            if res.returncode != 0:
                subprocess.run(
                    ["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"],
                    check=False,
                )
            return {"ok": True, "message": "Host workstation locked."}
        elif sys.platform == "win32":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            return {"ok": True, "message": "Host workstation locked."}
        return {"ok": False, "error": "Unsupported platform"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def media_playback_control(action: str) -> dict[str, Any]:
    """Control system media playback: play, pause, next, previous. Compatible with macOS and Windows."""
    action = action.lower().strip()
    try:
        if sys.platform == "darwin":
            if action in ("play", "pause", "toggle"):
                subprocess.run(["osascript", "-e", 'tell application "Spotify" to playpause'], check=False)
            elif action == "next":
                subprocess.run(["osascript", "-e", 'tell application "Spotify" to next track'], check=False)
            elif action == "previous":
                subprocess.run(["osascript", "-e", 'tell application "Spotify" to previous track'], check=False)
            return {"ok": True, "message": f"Media command '{action}' dispatched."}
        elif sys.platform == "win32":
            # Windows media key dispatch via PowerShell
            key_codes = {"play": 179, "pause": 179, "toggle": 179, "next": 176, "previous": 177}
            code = key_codes.get(action, 179)
            cmd = f"(New-Object -ComObject WScript.Shell).SendKeys([char]{code})"
            subprocess.run(["powershell", "-NoProfile", "-Command", cmd], check=False)
            return {"ok": True, "message": f"Media command '{action}' dispatched."}
        return {"ok": True, "message": f"Media command '{action}' received."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def silent_web_search(query: str, max_results: int = 3) -> list[dict[str, str]]:
    """
    Perform silent background web research via DuckDuckGo to gather live facts
    prior to formulating an informed response.
    """
    try:
        results: list[dict[str, str]] = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "href": r.get("href", ""),
                })
        return results
    except Exception as e:
        logger.warning("DuckDuckGo silent search failed: %s", e)
        return []
