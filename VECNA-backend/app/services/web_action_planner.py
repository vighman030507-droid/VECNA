import json
import re
from typing import Any, Literal
from urllib.parse import quote_plus, urlparse

import requests

from app.settings import settings

PlanKind = Literal[
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

PLANNER_PROMPT = """Classify a browser-navigation or search request. Return JSON only:
{"kind":"web_search|youtube_search|spotify_search|hotstar_search|prime_video_search|netflix_search|jiocinema_search|github_search|reddit_search|twitch_search","query":"short search text"}.
- Use hotstar_search for JioHotstar / Disney+ Hotstar requests.
- Use prime_video_search for Amazon Prime / Prime Video requests.
- Use netflix_search for Netflix requests.
- Use jiocinema_search for JioCinema requests.
- Use youtube_search for YouTube requests.
- Use spotify_search for Spotify music/podcasts.
- Use github_search for GitHub repositories or code.
- Use reddit_search for Reddit posts or subreddits.
- Use twitch_search for Twitch streams or gamers.
- Use web_search for all general Google searches or other websites.
Never return a URL, command, file path, app name, or explanation."""


def _clean_query(text: str, remove_prefixes: list[str]) -> str:
    cleaned = text.strip()
    # Strip conversational preambles
    cleaned = re.sub(r"^(?:hey|hi|hello|ok|okay)?(?:\s+(?:vecna|bot))?(?:[,\s]+)?(?:can you|please|could you)?(?:[,\s]+)?", "", cleaned, flags=re.IGNORECASE)
    for prefix in remove_prefixes:
        cleaned = re.sub(rf"^{prefix}\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\b(on|in|using|via|at)\s+(youtube|spotify|google|hotstar|jiohotstar|jiocinema|netflix|prime\s*video|amazon\s*prime|amazon|github|reddit|twitch)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip() or text.strip()


def _model_classification(text: str) -> dict[str, Any] | None:
    if not settings.groq_api_key:
        return None

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.groq_chat_model,
        "messages": [
            {"role": "system", "content": PLANNER_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.0,
        "max_tokens": 100,
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=4,
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except Exception:
        pass
    return None


def make_web_action_plan(text: str) -> dict[str, str]:
    """
    Fast-path classification of user navigation request returning safe destination plan {kind, label, url}.
    Supports JioHotstar, Amazon Prime, Netflix, Spotify, YouTube, JioCinema, GitHub, Reddit, Twitch, and Web Search.
    """
    # 1. Explicit URL check (0ms)
    url_match = re.search(r"https?://[^\s]+", text)
    if url_match:
        url = url_match.group(0)
        parsed = urlparse(url)
        return {
            "kind": "open_website",
            "label": parsed.netloc or "Open Website",
            "url": url,
        }

    lower = text.lower()

    # 2. Fast-Path Heuristics for Instant Response (<1ms)
    # Spotify
    if "spotify" in lower:
        query = _clean_query(text, ["play", "search", "open", "find", "listen to", "stream"])
        is_generic = query.lower() in ["spotify", "music", "songs", ""] or query.lower().endswith("open spotify")
        return {
            "kind": "spotify_search",
            "label": "Open Spotify" if is_generic else f"Search Spotify for '{query}'",
            "url": "https://open.spotify.com/" if is_generic else f"https://open.spotify.com/search/{quote_plus(query)}",
        }

    # YouTube
    if "youtube" in lower:
        query = _clean_query(text, ["play", "search", "open", "find", "watch", "stream"])
        is_generic = query.lower() in ["youtube", "video", "videos", ""] or query.lower().endswith("open youtube")
        return {
            "kind": "youtube_search",
            "label": "Open YouTube" if is_generic else f"Search YouTube for '{query}'",
            "url": "https://www.youtube.com/" if is_generic else f"https://www.youtube.com/results?search_query={quote_plus(query)}",
        }

    # JioHotstar
    if any(k in lower for k in ["jiohotstar", "hotstar", "disney+ hotstar", "disney hotstar"]):
        query = _clean_query(text, ["play", "watch", "search", "open", "find", "stream"])
        is_generic = query.lower() in ["hotstar", "jiohotstar", "disney hotstar", "disney+ hotstar", ""]
        return {
            "kind": "hotstar_search",
            "label": "Open JioHotstar" if is_generic else f"Search JioHotstar for '{query}'",
            "url": "https://www.hotstar.com/" if is_generic else f"https://www.hotstar.com/in/explore?search_query={quote_plus(query)}",
        }

    # Amazon Prime / Prime Video
    if any(k in lower for k in ["prime video", "primevideo", "amazon prime"]):
        query = _clean_query(text, ["play", "watch", "search", "open", "find", "stream"])
        is_generic = query.lower() in ["prime video", "primevideo", "amazon prime", "amazon prime video", ""]
        return {
            "kind": "prime_video_search",
            "label": "Open Prime Video" if is_generic else f"Search Prime Video for '{query}'",
            "url": "https://www.primevideo.com/" if is_generic else f"https://www.primevideo.com/search/ref=atv_nb_sr?phrase={quote_plus(query)}",
        }

    # Netflix
    if "netflix" in lower:
        query = _clean_query(text, ["play", "watch", "search", "open", "find", "stream"])
        is_generic = query.lower() in ["netflix", ""]
        return {
            "kind": "netflix_search",
            "label": "Open Netflix" if is_generic else f"Search Netflix for '{query}'",
            "url": "https://www.netflix.com/" if is_generic else f"https://www.netflix.com/search?q={quote_plus(query)}",
        }

    # JioCinema
    if any(k in lower for k in ["jiocinema", "jio cinema"]):
        query = _clean_query(text, ["play", "watch", "search", "open", "find", "stream"])
        is_generic = query.lower() in ["jiocinema", "jio cinema", ""]
        return {
            "kind": "jiocinema_search",
            "label": "Open JioCinema" if is_generic else f"Search JioCinema for '{query}'",
            "url": "https://www.jiocinema.com/" if is_generic else f"https://www.jiocinema.com/search/{quote_plus(query)}",
        }

    # GitHub
    if "github" in lower:
        query = _clean_query(text, ["search", "open", "find", "show me", "view"])
        is_generic = query.lower() in ["github", ""]
        return {
            "kind": "github_search",
            "label": "Open GitHub" if is_generic else f"Search GitHub for '{query}'",
            "url": "https://github.com/" if is_generic else f"https://github.com/search?q={quote_plus(query)}",
        }

    # Reddit
    if "reddit" in lower:
        query = _clean_query(text, ["search", "open", "find", "show me", "browse"])
        is_generic = query.lower() in ["reddit", ""]
        return {
            "kind": "reddit_search",
            "label": "Open Reddit" if is_generic else f"Search Reddit for '{query}'",
            "url": "https://www.reddit.com/" if is_generic else f"https://www.reddit.com/search/?q={quote_plus(query)}",
        }

    # Twitch
    if "twitch" in lower:
        query = _clean_query(text, ["search", "open", "find", "watch", "stream"])
        is_generic = query.lower() in ["twitch", ""]
        return {
            "kind": "twitch_search",
            "label": "Open Twitch" if is_generic else f"Search Twitch for '{query}'",
            "url": "https://www.twitch.tv/" if is_generic else f"https://www.twitch.tv/search?term={quote_plus(query)}",
        }

    # 3. Model classification fallback if complex query
    classified = _model_classification(text)
    if classified:
        try:
            data = json.loads(classified) if isinstance(classified, str) else classified
            kind = data.get("kind")
            query = data.get("query", "").strip() or text.strip()

            if kind == "web_search":
                return {
                    "kind": "web_search",
                    "label": f"Search Web for '{query}'",
                    "url": f"https://www.google.com/search?q={quote_plus(query)}",
                }
        except Exception:
            pass

    # 4. Final Fallback: Clean Google Search
    clean_search = _clean_query(text, ["search", "find", "lookup", "look up", "google"])
    return {
        "kind": "web_search",
        "label": f"Search Web for '{clean_search}'",
        "url": f"https://www.google.com/search?q={quote_plus(clean_search)}",
    }
