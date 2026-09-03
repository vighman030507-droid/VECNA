"""
Neural Hot-Swapping Provider Router for VECNA.
Enables automatic zero-downtime failover across Groq, Google Gemini, NVIDIA NIM, and Mistral AI.
If the primary provider hits a 429 rate limit or network outage, VECNA seamlessly transitions
to the next configured neural brain without breaking the conversation.
"""
from __future__ import annotations

import json
import logging
from typing import Any
import requests

from app.settings import settings

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"


class NeuralHotSwapError(RuntimeError):
    pass


def get_available_providers() -> list[dict[str, Any]]:
    """Return ordered fallback chain of configured AI inference providers."""
    providers: list[dict[str, Any]] = []

    # 1. Primary: Groq
    if settings.groq_api_key and not settings.groq_api_key.startswith("your_"):
        providers.append({
            "name": "Groq (Primary)",
            "url": GROQ_URL,
            "key": settings.groq_api_key,
            "models": [settings.groq_chat_model, "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"],
        })

    # 2. Backup 1: Google Gemini (OpenAI-compatible endpoint)
    if settings.gemini_api_key and not settings.gemini_api_key.startswith("your_"):
        providers.append({
            "name": "Google Gemini",
            "url": GEMINI_URL,
            "key": settings.gemini_api_key,
            "models": ["gemini-3-flash-preview", "gemini-flash-latest", "gemini-2.5-flash"],
        })

    # 3. Backup 2: NVIDIA NIM
    if settings.nvidia_api_key and not settings.nvidia_api_key.startswith("your_"):
        providers.append({
            "name": "NVIDIA NIM",
            "url": NVIDIA_URL,
            "key": settings.nvidia_api_key,
            "models": ["meta/llama-3.3-70b-instruct"],
        })

    # 4. Backup 3: Mistral AI
    if settings.mistral_api_key and not settings.mistral_api_key.startswith("your_"):
        providers.append({
            "name": "Mistral AI",
            "url": MISTRAL_URL,
            "key": settings.mistral_api_key,
            "models": ["mistral-small-latest"],
        })

    # 5. Generic Custom Backups
    if settings.backup_1_api_key and settings.backup_1_base_url and not settings.backup_1_api_key.startswith("your_"):
        base_url = settings.backup_1_base_url.rstrip("/")
        if not base_url.endswith("/chat/completions"):
            base_url = f"{base_url}/chat/completions"
        providers.append({
            "name": "Custom Backup 1",
            "url": base_url,
            "key": settings.backup_1_api_key,
            "models": [settings.backup_1_model or "default"],
        })

    if settings.backup_2_api_key and settings.backup_2_base_url and not settings.backup_2_api_key.startswith("your_"):
        base_url = settings.backup_2_base_url.rstrip("/")
        if not base_url.endswith("/chat/completions"):
            base_url = f"{base_url}/chat/completions"
        providers.append({
            "name": "Custom Backup 2",
            "url": base_url,
            "key": settings.backup_2_api_key,
            "models": [settings.backup_2_model or "default"],
        })

    return providers


def dispatch_completion(
    messages: list[dict[str, str]],
    temperature: float = 0.72,
    max_tokens: int = 1024,
) -> tuple[str, str]:
    """
    Executes a chat completion across the neural hot-swap chain.
    Returns (reply_text, active_provider_name).
    """
    providers = get_available_providers()
    if not providers:
        raise NeuralHotSwapError("No AI inference providers are configured with valid API keys.")

    last_error: Exception | None = None

    for prov in providers:
        prov_name = prov["name"]
        url = prov["url"]
        api_key = prov["key"]
        models = prov["models"]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        for model in models:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=25)
                if response.status_code == 200:
                    data = response.json()
                    choice = data.get("choices", [{}])[0]
                    msg_obj = choice.get("message", {})
                    reply = msg_obj.get("content", "").strip()
                    if not reply and msg_obj.get("reasoning"):
                        reply = msg_obj["reasoning"].strip()

                    if reply:
                        return reply, f"{prov_name} ({model})"

                # If rate-limited (429) or server error, hot-swap to next model/provider
                logger.warning(
                    "Provider %s (%s) returned HTTP %d: %s. Hot-swapping to fallback...",
                    prov_name,
                    model,
                    response.status_code,
                    response.text[:200],
                )
                last_error = NeuralHotSwapError(f"{prov_name} error: {response.status_code}")
            except requests.RequestException as exc:
                logger.warning("Provider %s connection failed: %s. Trying fallback...", prov_name, exc)
                last_error = exc

    raise last_error or NeuralHotSwapError("All neural providers in failover chain exhausted.")
