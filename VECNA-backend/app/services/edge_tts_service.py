import asyncio
import io
import re
# pyrefly: ignore [missing-import]
import edge_tts
# pyrefly: ignore [missing-import]
from pydub import AudioSegment

from app.schemas import Voice

VOICES = (
    Voice(id="en-US-GuyNeural",          label="Guy — US English"),
    Voice(id="en-US-ChristopherNeural",  label="Christopher (Deep) — US English"),
    Voice(id="en-GB-RyanNeural",         label="Ryan — UK English"),
    Voice(id="en-US-JennyNeural",        label="Jenny — US English"),
    Voice(id="hi-IN-MadhurNeural",       label="Madhur (Hindi/Hinglish) — India"),
    Voice(id="hi-IN-SwaraNeural",        label="Swara (Hindi Female) — India"),
)
VOICE_IDS = {v.id for v in VOICES}

# Per-language default voices & prosody
LANG_DEFAULTS: dict[str, dict[str, str]] = {
    "en": {"voice": "en-US-ChristopherNeural", "pitch": "-18Hz", "rate": "-8%"},
    "hi": {"voice": "hi-IN-MadhurNeural",      "pitch": "-18Hz", "rate": "-8%"},
}

DEFAULT_VOICE = "en-US-ChristopherNeural"
DEFAULT_PITCH = "-18Hz"
DEFAULT_RATE  = "-8%"


class EdgeTtsError(RuntimeError):
    pass


def available_voices() -> list[Voice]:
    return list(VOICES)


def clean_text_for_speech(text: str, max_chars: int = 1200) -> str:
    """Strip Zalgo marks, markdown syntax, and format text for smooth speech synthesis."""
    cleaned = re.sub(r"[\u0300-\u036f\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f]", "", text)
    # Strip markdown headers, horizontal rules, links, formatting
    cleaned = re.sub(r"#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"[-*_]{3,}", " ", cleaned)
    cleaned = re.sub(r"[*_~`#>]", "", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"^\s*[-+*]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)

    # Convert hyphens/dashes between alphanumeric characters into a space.
    # Microsoft Edge-TTS neural voices for Indian languages (hi-IN-MadhurNeural)
    # do not recognize hyphenated compound words like "upside-down" or "upside‑down"
    # and spell out each letter individually. Replacing with a space ensures natural pronunciation.
    dash_pattern = r"[-\u2010-\u2015\u2212\uFE58\uFE63\uFF0D\u00AD]"
    cleaned = re.sub(
        rf"(?<=[a-zA-Z0-9\u0900-\u097F]){dash_pattern}+(?=[a-zA-Z0-9\u0900-\u097F])",
        " ",
        cleaned,
    )
    # Specifically ensure Upside Down is pronounced as standard words
    cleaned = re.sub(r"(?i)\bupside\s*down\b", "Upside Down", cleaned)

    cleaned = cleaned.strip()

    # If the response is a long detailed essay, speak the first 1200 chars at a clean sentence boundary
    if len(cleaned) > max_chars:
        cutoff = -1
        for punct in ("।", ".", "!", "?", "\n"):
            pos = cleaned[:max_chars].rfind(punct)
            if pos > cutoff:
                cutoff = pos
        if cutoff > 250:
            cleaned = cleaned[:cutoff + 1]
        else:
            cleaned = cleaned[:max_chars]

    return cleaned.strip() or text.strip()


def _boost_vocal_clarity(raw_bytes: bytes) -> bytes:
    """
    Apply natural dual-voice demonic processing.
    Primary voice: +3dB
    Shadow track: -16dB, 2500Hz low-pass, 20ms delay
    """
    try:
        primary = AudioSegment.from_file(io.BytesIO(raw_bytes), format="mp3")
        primary = primary + 3.0

        # Create shadow track: ducked, delayed, and low-passed
        shadow = primary - 16.0
        shadow = shadow.low_pass_filter(2500)
        
        # 20ms Haas delay
        delay_ms = 20
        silence = AudioSegment.silent(duration=delay_ms, frame_rate=primary.frame_rate)
        shadow_delayed = silence + shadow
        
        # Mix them
        mixed = primary.overlay(shadow_delayed)
        
        out = io.BytesIO()
        mixed.export(out, format="mp3", bitrate="192k")
        return out.getvalue()
    except Exception:
        return raw_bytes


# ==============================================================================
# PHASE 3: THE MOUTH (High-Fidelity Neural TTS, language-aware)
# ==============================================================================
async def generate_speech(
    text: str,
    voice_id: str | None = None,
    pitch: str | None = None,
    rate: str | None = None,
    language: str = "en",
    anger_level: int = 0,
) -> bytes:
    """
    Synthesize text into crystal-clear MP3 audio using Microsoft Edge TTS.
    Routes to the correct neural voice for English or Hindi/Hinglish mode.
    Devanagari text is always spoken by hi-IN-MadhurNeural to prevent English voice crashes.
    """
    speech_text = clean_text_for_speech(text)

    has_devanagari = bool(re.search(r"[\u0900-\u097F]", speech_text))
    if has_devanagari:
        lang_cfg = LANG_DEFAULTS["hi"]
        resolved_voice = "hi-IN-MadhurNeural"
        fallback_chain: list[tuple[str, str, str]] = [
            ("hi-IN-MadhurNeural", "-18Hz", "-8%"),
            ("hi-IN-SwaraNeural",  "-18Hz", "-8%"),
        ]
    elif language == "hi":
        lang_cfg = LANG_DEFAULTS["hi"]
        resolved_voice = voice_id if (voice_id and voice_id.startswith("hi-")) else lang_cfg["voice"]
        fallback_chain = [
            (resolved_voice,        lang_cfg["pitch"], lang_cfg["rate"]),
            ("hi-IN-SwaraNeural",   lang_cfg["pitch"], lang_cfg["rate"]),
            ("en-US-ChristopherNeural", DEFAULT_PITCH, DEFAULT_RATE),
        ]
    else:
        lang_cfg = LANG_DEFAULTS["en"]
        resolved_voice = voice_id if (voice_id and voice_id in VOICE_IDS) else lang_cfg["voice"]
        fallback_chain = [
            (resolved_voice,        lang_cfg["pitch"], lang_cfg["rate"]),
            ("en-US-ChristopherNeural", DEFAULT_PITCH, DEFAULT_RATE),
            ("en-US-GuyNeural",         DEFAULT_PITCH, DEFAULT_RATE),
        ]

    # Anger modulation: angrier = lower pitch, slightly faster delivery
    if anger_level >= 50:
        resolved_pitch = "-30Hz"
        resolved_rate  = "+5%"
    else:
        resolved_pitch = pitch or lang_cfg["pitch"]
        resolved_rate  = rate  or lang_cfg["rate"]
    # De-duplicate while preserving order
    seen: set[str] = set()
    unique_chain: list[tuple[str, str, str]] = []
    for item in fallback_chain:
        if item[0] not in seen:
            seen.add(item[0])
            unique_chain.append(item)

    raw_bytes = b""
    last_error: Exception | None = None

    for v, p, r in unique_chain:
        try:
            communicate = edge_tts.Communicate(text=speech_text, voice=v, pitch=p, rate=r)
            audio = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio.extend(chunk["data"])
            if audio:
                raw_bytes = bytes(audio)
                break
        except Exception as err:
            last_error = err

    if not raw_bytes:
        raise EdgeTtsError(f"TTS synthesis failed on all voices: {last_error}")

    return await asyncio.to_thread(_boost_vocal_clarity, raw_bytes)
