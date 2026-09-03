"""
System Telemetry, Vision, Memory, and Tool Execution Endpoints for VECNA.
Provides system telemetry, Hawkins optical scanner (screen vision),
vector memory vault management, and autonomous system/web tool execution.
"""
from __future__ import annotations

import asyncio
from typing import Any
from fastapi import APIRouter, HTTPException, status

from app.schemas import (
    MemoryAddRequest,
    MemoryListResponse,
    SystemToolRequest,
    SystemToolResponse,
    TelemetryResponse,
)
from app.services.system_tools import (
    adjust_system_volume,
    lock_screen,
    media_playback_control,
    silent_web_search,
)
from app.services.telemetry import get_live_telemetry
from app.services.vector_memory import memory_vault

router = APIRouter(prefix="/api", tags=["system-telemetry"])


# ------------------------------------------------------------------------------
# 1. LIVE SYSTEM TELEMETRY
# ------------------------------------------------------------------------------
@router.get("/telemetry", response_model=TelemetryResponse)
async def get_telemetry() -> TelemetryResponse:
    """Return real-time CPU, RAM, battery/power, disk, and uptime metrics."""
    data = await asyncio.to_thread(get_live_telemetry)
    return TelemetryResponse(**data)


# ------------------------------------------------------------------------------
# 3. VECTOR MEMORY VAULT
# ------------------------------------------------------------------------------
@router.get("/memory", response_model=MemoryListResponse)
async def get_memories() -> MemoryListResponse:
    """Return all stored memories from the persistent vector vault."""
    items = memory_vault.get_all()
    return MemoryListResponse(memories=items)


@router.post("/memory/add")
async def add_memory(req: MemoryAddRequest) -> dict[str, Any]:
    """Permanently store a new user fact or preference in the Vecna memory vault."""
    result = memory_vault.remember(req.text)
    return result


# ------------------------------------------------------------------------------
# 4. AUTONOMOUS SYSTEM & WEB TOOLS
# ------------------------------------------------------------------------------
@router.post("/tools/execute", response_model=SystemToolResponse)
async def execute_tool(req: SystemToolRequest) -> SystemToolResponse:
    """Execute host workstation operations (volume, screen lock, media, web research)."""
    if req.tool == "volume":
        if req.level is None:
            raise HTTPException(status_code=400, detail="Volume level (0-100) is required.")
        res = adjust_system_volume(req.level)
        return SystemToolResponse(ok=res["ok"], message=res.get("message", res.get("error", "")))

    elif req.tool == "lock_screen":
        res = lock_screen()
        return SystemToolResponse(ok=res["ok"], message=res.get("message", res.get("error", "")))

    elif req.tool == "media":
        action = req.action or "play"
        res = media_playback_control(action)
        return SystemToolResponse(ok=res["ok"], message=res["message"])

    elif req.tool == "web_search":
        if not req.query:
            raise HTTPException(status_code=400, detail="Search query is required.")
        results = await asyncio.to_thread(silent_web_search, req.query, 3)
        return SystemToolResponse(
            ok=True,
            message=f"Retrieved {len(results)} search results.",
            data=results,
        )

    raise HTTPException(status_code=400, detail=f"Unknown tool: {req.tool}")
