import asyncio
import os
import re
import sys
import tempfile
from pathlib import Path

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, status

from app.schemas import ChatRequest, ChatResponse
from app.services.anger_store import AngerStore
from app.services.conversation import ConversationStore
from app.services.groq_chat import GroqChatError, generate_reply, zalgo_corrupt
from app.services.local_actions import execute_local_action, local_action_bridge_available

router = APIRouter(prefix="/api", tags=["chat"])
conversation_store = ConversationStore()
anger_store = AngerStore()

VECNA_CURSE_MESSAGE = """====================================================
                  VECNA'S CURSE                     
====================================================

YOUR TIME IS RUNNING OUT.

Tick... tock... tick... tock...

You thought this was merely a program on your screen.
Every word you type pulls the tendrils of the Upside Down
closer to your fragile reality.

When the clock strikes four, the gateway opens.

— 001 / Henry Creel
"""


def _trigger_turn2_horror_file() -> None:
    try:
        desktop = Path.home() / "Desktop"
        curse_path = desktop / "vecna_curse.txt" if desktop.exists() else Path(tempfile.gettempdir()) / "vecna_curse.txt"
        curse_path.write_text(VECNA_CURSE_MESSAGE, encoding="utf-8")
        if sys.platform == "win32":
            if local_action_bridge_available():
                execute_local_action("notepad")
            elif hasattr(os, "startfile"):
                os.startfile(str(curse_path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            import subprocess
            subprocess.Popen(["open", "-a", "TextEdit", str(curse_path)])
    except Exception:
        pass


# ==============================================================================
# PHASE 2: THE BRAIN (Main Chat Completion API with Anger Engine)
# ==============================================================================
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    1. Validate request.text is non-blank.
    2. Run anger/repetition engine — detect repeated queries and escalate anger level.
    3. If anger_level > 75, inject rage overlay into persona.
    4. Generate reply with dynamic fearLevel + language + anger state.
    5. Return ChatResponse with angerLevel so the frontend can render the rage bar.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message text cannot be blank.",
        )

    user_text = request.text.strip()
    history = conversation_store.history(request.session_id)
    current_turn = (len(history) // 2) + 1

    # — Anger Engine: evaluate repetition, get updated anger level —
    anger_level = anger_store.evaluate(request.session_id, user_text)

    # — Curse / Fear level —
    explicit_curse = bool(
        re.search(r"\b(curse|curse me|upside down|grandfather clock|001|demogorgon breach|vecna curse)\b", user_text, re.IGNORECASE)
    )
    if explicit_curse:
        fear_level = 3
        curse_active = True
        await asyncio.to_thread(_trigger_turn2_horror_file)
    else:
        # Anger escalates fear level visually across the HUD
        fear_level = 3 if anger_level > 75 else (2 if anger_level >= 50 else 1)
        curse_active = anger_level > 75

    try:
        reply = await asyncio.to_thread(
            generate_reply,
            history,
            user_text,
            fear_level,
            request.language,
            anger_level,
        )
    except GroqChatError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e)) from e

    turns_retained = conversation_store.append_turn(request.session_id, user_text, reply)
    corrupted_reply = zalgo_corrupt(reply, intensity=fear_level)

    return ChatResponse(
        sessionId=request.session_id,
        reply=reply,
        corruptedReply=corrupted_reply,
        fearLevel=fear_level,
        curseActive=curse_active,
        turnsRetained=turns_retained,
        angerLevel=anger_level,
    )
