"""
Hawkins Optical Scanner (Screen Vision) for VECNA.
Captures the host desktop screenshot and analyzes the active workspace
using multimodal visual models (Groq Vision, Gemini Vision, or NVIDIA Vision).
"""
from __future__ import annotations

import base64
import io
import logging
from typing import Any
from PIL import Image, ImageGrab
import requests

from app.settings import settings

logger = logging.getLogger(__name__)


def capture_screen_base64(max_width: int = 1280) -> str:
    """Capture desktop screenshot and return as base64 JPEG string."""
    screenshot = ImageGrab.grab()
    if screenshot.width > max_width:
        ratio = max_width / float(screenshot.width)
        new_height = int(float(screenshot.height) * float(ratio))
        screenshot = screenshot.resize((max_width, new_height), Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    # Convert RGBA to RGB if needed
    if screenshot.mode in ("RGBA", "P"):
        screenshot = screenshot.convert("RGB")
    screenshot.save(buffer, format="JPEG", quality=82)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def analyze_desktop(query: str = "Analyze what is currently open on my screen.") -> str:
    """
    Captures desktop screenshot and requests visual analysis from configured vision models.
    """
    try:
        b64_img = capture_screen_base64()
    except Exception as e:
        logger.error("Failed to capture screen: %s", e)
        return f"Optical sensor error: Failed to capture desktop frame ({e})."

    prompt = (
        "You are Vecna / Henry Creel observing the mortal's desktop screen. "
        "Analyze the screenshot provided. Describe what applications, code, browser tabs, or documents "
        "the user is currently working on. Offer chilling, intelligent commentary in character as Vecna. "
        f"User query: {query}"
    )

    # 1. Try Groq Vision
    if settings.groq_api_key and not settings.groq_api_key.startswith("your_"):
        try:
            headers = {
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "llama-3.2-11b-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                            },
                        ],
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 512,
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                reply = res.json()["choices"][0]["message"]["content"].strip()
                if reply:
                    return reply
        except Exception as e:
            logger.warning("Groq vision failed, trying fallback: %s", e)

    # 2. Try Gemini Vision
    if settings.gemini_api_key and not settings.gemini_api_key.startswith("your_"):
        try:
            headers = {
                "Authorization": f"Bearer {settings.gemini_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "gemini-2.5-flash",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                            },
                        ],
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 512,
            }
            res = requests.post("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                reply = res.json()["choices"][0]["message"]["content"].strip()
                if reply:
                    return reply
        except Exception as e:
            logger.warning("Gemini vision failed: %s", e)

    return "I gaze into your fragile screen, mortal, but my visual conduit is obstructed. Configure a valid vision API key to unlock the Eye of Vecna."
