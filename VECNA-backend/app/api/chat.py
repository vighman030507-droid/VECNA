import asyncio
import re

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, status

from app.schemas import ChatRequest, ChatResponse
from app.services.anger_store import AngerStore
from app.services.conversation import ConversationStore
from app.services.groq_chat import GroqChatError, generate_reply, zalgo_corrupt

router = APIRouter(prefix="/api", tags=["chat"])
conversation_store = ConversationStore()
anger_store = AngerStore()


# ==============================================================================
# PHASE 2: THE BRAIN (Main Chat Completion API with Anger Engine)
# ==============================================================================
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    user_text = request.text.strip()
    if not user_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text must not be blank.",
        )

    # — Context / Memory —
    history = conversation_store.history(request.session_id)

    # — Anger state tracking —
    anger_level = anger_store.evaluate(request.session_id, user_text)

    # — Curse / Fear level —
    explicit_curse = bool(
        re.search(r"\b(curse|curse me|upside down|grandfather clock|001|demogorgon breach|vecna curse)\b", user_text, re.IGNORECASE)
    )
    if explicit_curse:
        fear_level = 3
        curse_active = True
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
