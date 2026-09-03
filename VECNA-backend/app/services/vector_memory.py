"""
Persistent Vector Memory Vault for VECNA.
Enables long-term semantic memory recall (RAG) across restarts.
Stores user preferences, identity facts, and knowledge in JSON with similarity ranking.
"""
from __future__ import annotations

import datetime
import json
import logging
import math
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
MEMORY_FILE = DATA_DIR / "vecna_memory.json"


def _tokenize(text: str) -> list[str]:
    """Tokenize and normalize text into word stems/tokens."""
    clean = re.sub(r"[^\w\s\u0900-\u097F]", " ", text.lower())
    return [w for w in clean.split() if len(w) > 2]


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Compute cosine similarity between two term-frequency vectors."""
    intersection = set(vec_a.keys()) & set(vec_b.keys())
    numerator = sum(vec_a[x] * vec_b[x] for x in intersection)

    sum1 = sum(v ** 2 for v in vec_a.values())
    sum2 = sum(v ** 2 for v in vec_b.values())
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    return float(numerator) / denominator


class VectorMemoryVault:
    """Lightweight, persistent memory store with TF-IDF semantic recall."""

    def __init__(self, filepath: Path = MEMORY_FILE) -> None:
        self.filepath = filepath
        self.memories: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
            except Exception as e:
                logger.error("Failed to load memory file: %s", e)
                self.memories = []
        else:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            self.memories = []
            self._seed_default_memories()

    def _save(self) -> None:
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save memory file: %s", e)

    def _seed_default_memories(self) -> None:
        """Seed essential developer and system facts."""
        seeds = [
            "Creator is Vighnesh Singh, a 2nd year student studying Automation and Robotics Engineering at VESIT Mumbai.",
            "Vighnesh's email is vighman030507@gmail.com and contact number is 7304252207.",
            "VECNA is an advanced voice assistant inspired by JARVIS from Iron Man (Marvel), wrapped in the supernatural entity Vecna / Henry Creel from Stranger Things (Netflix).",
            "VECNA possesses multimodal intelligence: audio speech synthesis, real-time speech transcription, screen vision, and autonomous actions.",
        ]
        for s in seeds:
            self.remember(s)

    def remember(self, text: str) -> dict[str, Any]:
        """Store a new memory item."""
        text_clean = text.strip()
        if not text_clean:
            return {"ok": False, "error": "Cannot remember empty text."}

        # Check for duplicates
        for m in self.memories:
            if m["text"].lower() == text_clean.lower():
                return {"ok": True, "message": "Memory already exists in vault."}

        tokens = _tokenize(text_clean)
        tf: dict[str, float] = {}
        for tok in tokens:
            tf[tok] = tf.get(tok, 0.0) + 1.0

        item = {
            "id": len(self.memories) + 1,
            "text": text_clean,
            "vector": tf,
            "created_at": datetime.datetime.now().isoformat(),
        }
        self.memories.append(item)
        self._save()
        return {"ok": True, "message": "Memory permanently recorded in Vecna vault.", "item": item}

    def recall(self, query: str, top_k: int = 3, threshold: float = 0.15) -> list[str]:
        """Recall top_k relevant memories matching query."""
        if not query or not self.memories:
            return []

        q_tokens = _tokenize(query)
        if not q_tokens:
            return []

        q_vec: dict[str, float] = {}
        for tok in q_tokens:
            q_vec[tok] = q_vec.get(tok, 0.0) + 1.0

        scored: list[tuple[float, str]] = []
        for m in self.memories:
            sim = _cosine_similarity(q_vec, m.get("vector", {}))
            if sim >= threshold:
                scored.append((sim, m["text"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored[:top_k]]

    def get_all(self) -> list[dict[str, Any]]:
        """Return all memories."""
        return [{"id": m["id"], "text": m["text"], "created_at": m.get("created_at", "")} for m in self.memories]

    def clear(self) -> None:
        """Clear memory vault."""
        self.memories = []
        self._save()


# Global singleton
memory_vault = VectorMemoryVault()
