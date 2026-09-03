"""
Live System Telemetry Service for VECNA.
Captures real-time CPU, RAM, Battery/Power, and System Metrics using psutil.
Feeds live diagnostic telemetry into the Hawkins System Status HUD.
"""
from __future__ import annotations

import datetime
import logging
import time
from typing import Any
import psutil

logger = logging.getLogger(__name__)

_cached_weather: dict[str, Any] = {"condition": "Clear", "temp": "--", "timestamp": 0}


def get_live_telemetry() -> dict[str, Any]:
    """Capture real-time host machine metrics."""
    try:
        cpu = round(psutil.cpu_percent(interval=None), 1)
        ram = psutil.virtual_memory()
        
        battery = psutil.sensors_battery()
        if battery:
            power_pct = round(battery.percent, 1)
            power_status = "Charging" if battery.power_plugged else f"{power_pct}% (Battery)"
        else:
            power_pct = 100.0
            power_status = "AC Power (100%)"

        disk = psutil.disk_usage("/")

        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M:%S %p")
        date_str = now.strftime("%A, %b %d, %Y")

        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime_delta = now - boot_time
        hours, remainder = divmod(int(uptime_delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m"

        return {
            "cpu_percent": cpu,
            "ram_percent": round(ram.percent, 1),
            "ram_used_gb": round(ram.used / (1024 ** 3), 2),
            "ram_total_gb": round(ram.total / (1024 ** 3), 2),
            "power_percent": power_pct,
            "power_status": power_status,
            "disk_percent": round(disk.percent, 1),
            "disk_free_gb": round(disk.free / (1024 ** 3), 1),
            "system_time": time_str,
            "system_date": date_str,
            "uptime": uptime_str,
        }
    except Exception as e:
        logger.error("Failed to capture system telemetry: %s", e)
        return {
            "cpu_percent": 0.0,
            "ram_percent": 0.0,
            "ram_used_gb": 0.0,
            "ram_total_gb": 0.0,
            "power_percent": 100.0,
            "power_status": "Unknown",
            "disk_percent": 0.0,
            "disk_free_gb": 0.0,
            "system_time": "--:--:--",
            "system_date": "",
            "uptime": "--",
        }
