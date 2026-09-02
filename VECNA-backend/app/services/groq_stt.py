import io
import re
import requests

from app.settings import settings
from pydub import AudioSegment

GROQ_TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

# Common Whisper silence / background noise hallucinations to filter out
WHISPER_HALLUCINATIONS = {
    "thank you",
    "thank you.",
    "thank you very much.",
    "thanks for watching",
    "thanks for watching.",
    "thank you for watching.",
    "subtitles by",
    "amara.org",
    "subtitles by the amara.org community",
    "you",
    "you.",
    "bye",
    "bye.",
    "mbc",
    "please subscribe",
    "subscribe",
    "see you next time",
    "see you next time.",
    "...",
    ".",
    "silence",
    "[silence]",
}


class GroqSttError(RuntimeError):
    pass


def _detect_audio_container(audio: bytes, default_filename: str, default_content_type: str) -> tuple[str, str]:
    """
    Detect the real audio format from magic bytes to guarantee Groq Whisper compatibility.
    """
    if len(audio) >= 4:
        if audio[:4] == b"\x1a\x45\xdf\xa3":
            return "audio.webm", "audio/webm"
        if audio[:4] == b"RIFF":
            return "audio.wav", "audio/wav"
        if audio[:4] == b"OggS":
            return "audio.ogg", "audio/ogg"
    if len(audio) >= 8 and audio[4:8] == b"ftyp":
        return "audio.mp4", "audio/mp4"
    if len(audio) >= 3 and (audio[:3] == b"ID3" or audio[:2] in (b"\xff\xfb", b"\xff\xf3")):
        return "audio.mp3", "audio/mpeg"

    # Fallback to extension or content-type
    ext = default_filename.split(".")[-1].lower() if "." in default_filename else "webm"
    if ext in ("webm", "wav", "ogg", "mp3", "mp4", "m4a"):
        return f"audio.{ext}", default_content_type
    return "audio.webm", "audio/webm"


# ==============================================================================
# PHASE 1: THE EARS (Speech-to-Text with Groq Whisper)
# ==============================================================================
def transcribe(audio: bytes, filename: str, content_type: str, language: str = "en") -> str:
    """
    Send user audio recording bytes to Groq Whisper and return transcribed text.
    Uses temperature=0.0 and prompt conditioning to eliminate hallucinations.
    Accepts language='en' or 'hi' to guide Whisper's acoustic model and prompt.
    """
    if not settings.groq_api_key:
        raise GroqSttError("Groq is not configured.")

    if not audio or len(audio) < 800:
        return "Didn't hear you."

    try:
        audio_segment = AudioSegment.from_file(io.BytesIO(audio))
        audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
        peak = audio_segment.max_dBFS
        if peak < 0:
            audio_segment = audio_segment.apply_gain(-peak)
        out_buf = io.BytesIO()
        audio_segment.export(out_buf, format="wav")
        processed_audio = out_buf.getvalue()
        real_filename = "audio.wav"
        real_content_type = "audio/wav"
    except Exception:
        processed_audio = audio
        real_filename, real_content_type = _detect_audio_container(processed_audio, filename, content_type)

    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
    files = {"file": (real_filename, io.BytesIO(processed_audio), real_content_type)}

    # Build language-appropriate Whisper prompt context
    if language == "hi":
        whisper_prompt = (
            "Transcribe the following audio accurately. "
            "The speaker may use Hindi (Devanagari), Hinglish (Hindi written in Roman script mixed with English), "
            "or pure English. Preserve all words exactly as spoken. "
            "Do not translate or summarize. Write Hindi words in their natural script or Roman transliteration as spoken."
        )
    else:
        whisper_prompt = (
            "Transcribe the following audio in English, Hindi, or Hinglish written in Roman script. "
            "Preserve all words exactly as spoken. Do not translate or summarize."
        )

    data = {
        "model": "whisper-large-v3-turbo",
        "temperature": "0.0",
        "prompt": whisper_prompt,
        "response_format": "json",
    }
    # Whisper language hint: pass 'hi' for Hindi so the acoustic model is primed correctly
    if language == "hi":
        data["language"] = "hi"

    try:
        response = requests.post(
            GROQ_TRANSCRIBE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=25,
        )
    except requests.RequestException as e:
        raise GroqSttError(f"Speech transcription request failed: {e}") from e

    if response.status_code == 400:
        err_body = response.json() if response.content else {}
        err_msg = err_body.get("error", {}).get("message", "Invalid audio format or empty recording.")
        raise GroqSttError(f"Could not process audio: {err_msg}")

    if response.status_code != 200:
        raise GroqSttError(f"Groq Whisper transcription failed: {response.text}")

    result = response.json()
    raw_text = result.get("text", "").strip()

    # Clean hallucination filter
    normalized = raw_text.lower().strip()
    if normalized in WHISPER_HALLUCINATIONS:
        return "Didn't hear you."

    # Strip repetitive subtitle credits
    if "subtitles by" in normalized or "amara.org" in normalized:
        return "Didn't hear you."

    # Punctuation-only check
    if re.fullmatch(r"[\W_]+", raw_text) or not raw_text:
        return "Didn't hear you."

    return raw_text
