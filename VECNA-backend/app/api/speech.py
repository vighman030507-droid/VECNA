import asyncio

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status

from app.schemas import TranscriptResponse, TtsRequest, VoicesResponse
from app.services.edge_tts_service import (
    DEFAULT_VOICE,
    EdgeTtsError,
    available_voices,
    generate_speech,
)
from app.services.groq_stt import GroqSttError, transcribe

router = APIRouter(prefix="/api", tags=["speech"])

ALLOWED_AUDIO_PREFIXES = ("audio/", "application/octet-stream")
MAX_AUDIO_BYTES = 10 * 1024 * 1024


# ==============================================================================
# PHASE 3: THE MOUTH (Voice Catalog Endpoint)
# ==============================================================================
@router.get("/voices", response_model=VoicesResponse)
async def voices() -> VoicesResponse:
    """
    Return available Edge-TTS neural voices.
    """
    return VoicesResponse(voices=available_voices())


# ==============================================================================
# PHASE 3: THE MOUTH (Text-to-Speech Streaming Endpoint)
# ==============================================================================
@router.post("/tts", response_class=Response)
async def tts(request: TtsRequest) -> Response:
    """
    Convert reply text into MP3 audio stream with deep demonic voice processing.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text cannot be blank.",
        )

    voice_id = request.voice_id if request.voice_id else DEFAULT_VOICE

    try:
        audio = await generate_speech(
            request.text.strip(),
            voice_id=voice_id,
            language=request.language,
            anger_level=request.anger_level,
        )
    except EdgeTtsError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"TTS error: {e}") from e

    return Response(content=audio, media_type="audio/mpeg")


# ==============================================================================
# PHASE 1: THE EARS (Audio Transcription Upload Endpoint)
# ==============================================================================
@router.post("/transcribe", response_model=TranscriptResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form("en"),
) -> TranscriptResponse:
    """
    Accept microphone audio recording and return transcribed text via Groq Whisper.
    Supports all browser audio formats including audio/webm; codecs=opus.
    language: 'en' (default) or 'hi' (Hindi/Hinglish) — guides Whisper acoustic model.
    """
    raw_content_type = audio.content_type or "audio/webm"
    base_mime = raw_content_type.split(";")[0].strip().lower()

    if not any(base_mime.startswith(prefix) for prefix in ALLOWED_AUDIO_PREFIXES):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio type: {raw_content_type}",
        )

    payload = await audio.read()
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Audio payload is empty.",
        )

    if len(payload) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio payload exceeds 10MB limit.",
        )

    filename = audio.filename or "recording.webm"
    if "." not in filename:
        filename = f"{filename}.webm"

    try:
        transcript = await asyncio.to_thread(
            transcribe,
            payload,
            filename,
            base_mime,
            language,
        )
    except GroqSttError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e

    return TranscriptResponse(transcript=transcript)
