from typing import Any, Literal
from uuid import UUID

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: UUID = Field(alias="sessionId")
    text: str = Field(min_length=1, max_length=50_000)
    language: str = "en"


class ChatResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: UUID = Field(alias="sessionId")
    reply: str
    corrupted_reply: str = Field(alias="corruptedReply")
    fear_level: int = Field(alias="fearLevel", ge=1, le=3)
    curse_active: bool = Field(alias="curseActive")
    turns_retained: int = Field(alias="turnsRetained", ge=0, le=6)
    anger_level: int = Field(alias="angerLevel", ge=0, le=100)


class Voice(BaseModel):
    id: str
    label: str


class VoicesResponse(BaseModel):
    voices: list[Voice]


class TtsRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str = Field(min_length=1, max_length=50_000)
    voice_id: str = Field(default="en-US-ChristopherNeural", alias="voiceId")
    language: str = "en"
    anger_level: int = Field(default=0, alias="angerLevel", ge=0, le=100)


class TranscriptResponse(BaseModel):
    transcript: str


class WebActionPlanRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000)


class WebActionPlanResponse(BaseModel):
    kind: Literal[
        "open_website",
        "web_search",
        "youtube_search",
        "spotify_search",
        "hotstar_search",
        "prime_video_search",
        "netflix_search",
        "jiocinema_search",
        "github_search",
        "reddit_search",
        "twitch_search",
    ]
    label: str = Field(min_length=1, max_length=160)
    url: str = Field(min_length=1, max_length=2_000)


class LocalActionPlanRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000)


class LocalActionPlanResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    kind: Literal["open_local_app"]
    app_id: Literal["calculator", "notepad", "file_explorer", "vscode"] = Field(alias="appId")
    label: str = Field(min_length=1, max_length=160)
    requires_confirmation: bool = Field(alias="requiresConfirmation")


class LocalActionExecuteRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    app_id: Literal["calculator", "notepad", "file_explorer", "vscode"] = Field(alias="appId")
    confirmed: Literal[True]


class LocalActionExecuteResponse(BaseModel):
    ok: bool
    message: str


class LocalActionStatusResponse(BaseModel):
    enabled: bool


# ==============================================================================
# VECNA ADVANCED SYSTEM & TELEMETRY SCHEMAS
# ==============================================================================
class TelemetryResponse(BaseModel):
    cpu_percent: float
    ram_percent: float
    ram_used_gb: float
    ram_total_gb: float
    power_percent: float
    power_status: str
    disk_percent: float
    disk_free_gb: float
    system_time: str
    system_date: str
    uptime: str


class ScreenAnalyzeRequest(BaseModel):
    query: str = "Analyze what is currently open on my screen."


class ScreenAnalyzeResponse(BaseModel):
    analysis: str


class MemoryAddRequest(BaseModel):
    text: str = Field(min_length=3, max_length=5000)


class MemoryItem(BaseModel):
    id: int
    text: str
    created_at: str


class MemoryListResponse(BaseModel):
    memories: list[MemoryItem]


class SystemToolRequest(BaseModel):
    tool: Literal["volume", "lock_screen", "media", "web_search"]
    level: int | None = None
    action: str | None = None
    query: str | None = None


class SystemToolResponse(BaseModel):
    ok: bool
    message: str
    data: Any | None = None

