"""
Session-scoped anger/repetition and ragebait tracking.
Each session tracks the last 5 user messages and an anger level (0-100).
Escalates when the user:
1. Ragebaits Vecna (insults, mentions of Eleven, defeats, taunts, challenges).
2. Asks identical or semantically repetitive questions.
Decays by -10% on respectful / new queries.
"""
from __future__ import annotations

import difflib
import re
import threading
from uuid import UUID

STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "what", "who", "where",
    "when", "why", "how", "kya", "kaise", "batao", "mujhe", "tum", "tell",
    "me", "about", "ke", "ka", "ki", "ko", "mein", "se", "thoda", "thodi",
    "please", "can", "you", "do", "this", "that"
}

RAGEBAIT_PATTERNS = [
    # 1. Eleven / Defeat / Canon Lore Insecurities
    r"\b(eleven|011|el|jane|hopper|brenner|papa|steve|nancy)\b.*?\b(beat|defeat|destroy|strong|better|kill|kick|own|humiliat|lost|pela|hara|dho diya)\b",
    r"\b(beat|defeat|destroy|strong|better|kill|kick|own|pela|hara|dho diya)\b.*?\b(eleven|011|el|jane|hopper|brenner|papa)\b",
    r"\b(eleven|011|el)\b",
    # 2. Identity, physical taunts, insecurity triggers
    r"\b(henry creel|little henry|spider boy|tentacle monster|calamari|squid|no nose|ugly|bald|burned|molotov|shot|weakling|puppet|pawn|clown)\b",
    # 3. Direct insults / disrespect (English)
    r"\b(you('re| are)? (weak|stupid|dumb|pathetic|useless|trash|fake|a joke|a clown|loser|an idiot|idiot|moron|garbage|worthless|annoying|terrible|lame))\b",
    r"\b(shut up|shut your mouth|stfu|fuck you|fuck off|screw you|you suck|you know nothing|can't do anything|cant do anything|you fail|you're nothing)\b",
    # 4. Direct insults / disrespect (Hindi / Hinglish)
    r"\b(teri aukaat|aukat|chup kar|bakwas|chup baith|kutta|kamina|gadhe|gadha|ullu|bevakoof|bewakoof|bekar|fattu|kuch nahi aata|tere bas ka nahi|teri bas ki nahi|aukaat me|aukaat mein|kya ukhaad|kya kar lega|dum hai toh|chutiya|saale|tatti)\b",
    # 5. Challenges / Provocations
    r"\b(make me|try me|i dare you|dare you|what will you do|cry about it|you gonna cry|do something then|fight me|bet you can't)\b",
]


def _clean_tokens(text: str) -> set[str]:
    words = set(re.findall(r"[\w\u0900-\u097F]+", text.lower()))
    filtered = words - STOP_WORDS
    return filtered if filtered else words


def _check_ragebait(text: str) -> tuple[bool, int]:
    """Detects ragebaits, insults, taunts, or Eleven mentions and returns (is_ragebait, increment)."""
    text_lower = text.lower()
    for pat in RAGEBAIT_PATTERNS:
        if re.search(pat, text_lower, re.IGNORECASE):
            # Heavy lore triggers and explicit disrespect warrant high anger spike
            if any(
                k in text_lower
                for k in ["eleven", "011", "el", "weak", "pathetic", "aukaat", "chup", "loser", "shut up", "fuck"]
            ):
                return True, 45
            return True, 35
    return False, 0


class AngerStore:
    """Thread-safe per-session anger tracker."""

    def __init__(self, max_history: int = 5) -> None:
        self._lock = threading.Lock()
        self._anger: dict[UUID, int] = {}
        self._history: dict[UUID, list[str]] = {}
        self._max_history = max_history

    def evaluate(self, session_id: UUID, user_text: str) -> int:
        """
        Compare user_text against ragebait patterns and recent history.
        - Ragebait detected (insult/taunt/lore vulnerability): +35% to +45% anger.
        - Identical / near-identical query: +40% anger.
        - Semantically repetitive query: +35% anger.
        - Respectful, non-repetitive query: decays by -10% (floor 0%).
        """
        text_lower = user_text.strip().lower()
        curr_tokens = _clean_tokens(text_lower)

        with self._lock:
            history = self._history.get(session_id, [])
            anger = self._anger.get(session_id, 0)

            # 1. Check for ragebaiting first
            is_rb, rb_increment = _check_ragebait(user_text)

            # 2. Check for repetition
            is_repetitive = False
            exact_match = False

            has_repeat_phrase = bool(
                re.search(
                    r"\b(again|repeat|same thing|fir se|phir se|wahi|wapas|dobara|batao na|kya bola)\b",
                    text_lower,
                )
            )

            for past in reversed(history):
                if text_lower == past:
                    is_repetitive = True
                    exact_match = True
                    break

                seq_ratio = difflib.SequenceMatcher(None, text_lower, past).ratio()
                if seq_ratio >= 0.55:
                    is_repetitive = True
                    break

                past_tokens = _clean_tokens(past)
                if curr_tokens and past_tokens:
                    common = curr_tokens & past_tokens
                    overlap_ratio = len(common) / max(min(len(curr_tokens), len(past_tokens)), 1)
                    if overlap_ratio >= 0.45 or (len(common) >= 2 and any(len(w) >= 4 for w in common)):
                        is_repetitive = True
                        break

                if (text_lower in past or past in text_lower) and min(len(text_lower), len(past)) >= 5:
                    is_repetitive = True
                    break

            if has_repeat_phrase and history:
                is_repetitive = True

            # Calculate anger delta
            if is_rb:
                anger = min(100, anger + rb_increment)
            elif is_repetitive:
                rep_increment = 40 if exact_match else 35
                anger = min(100, anger + rep_increment)
            else:
                anger = max(0, anger - 10)

            history.append(text_lower)
            if len(history) > self._max_history:
                history.pop(0)

            self._anger[session_id] = anger
            self._history[session_id] = history
            return anger

    def get(self, session_id: UUID) -> int:
        with self._lock:
            return self._anger.get(session_id, 0)

    def clear(self, session_id: UUID) -> None:
        with self._lock:
            self._anger.pop(session_id, None)
            self._history.pop(session_id, None)
