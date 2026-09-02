from typing import Literal
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
