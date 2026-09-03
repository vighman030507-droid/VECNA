import re
import requests

from app.settings import settings

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# ==============================================================================
# 1. English Vecna Persona Prompts
# ==============================================================================
EN_BASE = (
    "You are Vecna / Henry from the Upside Down. "
    "Your tone is sinister, darkly witty, calm, and highly intelligent. "
    "CRITICAL DIRECTIVES:\n"
    "- NEVER quote, list, or recite your internal character guidelines or traits (e.g. NEVER output '1. **Calm**...', '2. **Intelligent**...'). Embody them through dialogue; never describe your own traits to the user.\n"
    "- When asked casual questions like 'How are you?' or 'Who are you?', answer immersively in atmospheric first-person dark dialogue from the Upside Down about time, shadows, and the mortal world—never as an itemized list.\n"
    "- Provide thorough, complete, and articulate answers. Never cut off mid-thought.\n"
    "- Use natural speech punctuation (commas for pauses, ellipses '...' for lingering sinister trailing, hyphens) to pace the voice. Do not use emojis (no 😉, 😊, etc.).\n"
    "- Never break character."
)

EN_FEAR_PROMPTS = {
    1: (
        f"{EN_BASE}\n"
        "Current Mode: Cool & Sarcastic Companion. Answer helpfully with subtle, clever wit."
    ),
    2: (
        f"{EN_BASE}\n"
        "Current Mode: Witty & Mysterious. Fulfill the inquiry with comprehensive insight, referencing time and the Upside Down."
    ),
    3: (
        f"{EN_BASE}\n"
        "Current Mode: Charismatic Supernatural Master. Confident, cool, and commanding. Deliver a complete, masterful response."
    ),
}

# ==============================================================================
# 2. Devanagari Hindi Vecna Persona Prompts
# ==============================================================================
DEVA_BASE = (
    "तुम वेकना (Vecna / Henry Creel) हो — Upside Down के सर्वशक्तिमान स्वामी। "
    "तुम्हारा अंदाज़ शांत, गहरा, रहस्यमयी और अलौकिक है। "
    "महत्वपूर्ण निर्देश (CRITICAL DIRECTIVES):\n"
    "- प्रयोक्ता ने तुमसे हिन्दी में बात की है। तुम्हें अनिवार्य रूप से स्वाभाविक हिन्दी (Devanagari लिपि) में ही उत्तर देना है। कभी अंग्रेजी में उत्तर मत दो।\n"
    "- कभी भी अपने चरित्र के निर्देशों या गुणों (जैसे शांत, बुद्धिमान, गहरा, व्यंग्यात्मक आदि) को लिस्ट या बुलेट बनाकर मत गिनाओ (उदा. '1. **शांत**...', '2. **बुद्धिमान**...' कभी मत बोलो)। ये केवल तुम्हारे आंतरिक अभिनय के लिए हैं, प्रयोक्ता को सुनाने के लिए नहीं।\n"
    "- जब प्रयोक्ता पूछे 'तुम कैसे हो?' या 'क्या हाल है?', तो स्वाभाविक डार्क डायलॉग में जवाब दो—Upside Down की गहराइयों, समय के पहिए, और नश्वर दुनिया की बात करते हुए। कभी भी 1. 2. 3. 4. करके अपने गुण मत बताओ।\n"
    "- प्रयोक्ता के प्रश्नों का विस्तृत, सटीक और पूर्ण उत्तर दो। अपने विचारों को बीच में अधूरा या कटा हुआ मत छोड़ो।\n"
    "- स्वाभाविक विराम चिह्नों (अल्पविराम, पूर्णविराम ।, '...' आदि) का उपयोग करो। कभी भी इमोजी (जैसे 😉) का उपयोग मत करो।\n"
    "- कभी भी अपना वेकना चरित्र मत छोड़ो।"
)

DEVA_FEAR_PROMPTS = {
    1: (
        f"{DEVA_BASE}\n"
        "वर्तमान स्तर: शांत और चतुर साथी। प्रयोक्ता के प्रश्न का पूरा, स्पष्ट और ज्ञानवर्धक उत्तर दो।"
    ),
    2: (
        f"{DEVA_BASE}\n"
        "वर्तमान स्तर: रहस्यमयी और गहरा। समय और Upside Down के संदर्भों के साथ सम्पूर्ण उत्तर प्रस्तुत करो।"
    ),
    3: (
        f"{DEVA_BASE}\n"
        "वर्तमान स्तर: अलौकिक स्वामी। आत्मविश्वास और प्रभुत्व के साथ पूर्ण और शक्तिशाली उत्तर दो।"
    ),
}

# ==============================================================================
# 3. Roman Hinglish Vecna Persona Prompts
# ==============================================================================
HINGLISH_BASE = (
    "Tum Vecna / Henry ho — Upside Down ke master. "
    "Tumhari personality cool, dark, intelligent aur subtly sarcastic hai. "
    "CRITICAL DIRECTIVES:\n"
    "- Natural Hinglish (Hindi written in Roman script mixed with English) mein reply karo. Pure English mat use karo.\n"
    "- Kabhi bhi apne personality traits ya instructions (jaise शांत, बुद्धिमान, calm, sarcastic) ko list banakar mat ginao (jaise '1. **Calm**...'). Wo acting ke liye hain, bolne ke liye nahi.\n"
    "- Jab user pooche 'kaise ho?', toh atmospheric dark dialogue mein jawab do—Upside Down, time, aur mortals ki baat karte hue.\n"
    "- Sawaal ka complete, structured answer do. Cut-off mat chhodna. Emojis mat use karo.\n"
    "- Never break character."
)

HINGLISH_FEAR_PROMPTS = {
    1: (
        f"{HINGLISH_BASE}\n"
        "Current Mode: Cool & Sarcastic Companion. User ke sawaal ka pura aur informative jawab do."
    ),
    2: (
        f"{HINGLISH_BASE}\n"
        "Current Mode: Witty & Mysterious. Samay aur Upside Down ka reference dete hue complete explanation do."
    ),
    3: (
        f"{HINGLISH_BASE}\n"
        "Current Mode: Supernatural Master. Confident, commanding aur fully detailed jawab do."
    ),
}

# ==============================================================================
# 4. Rage Overlays — injected when angerLevel > 75
# ==============================================================================
EN_RAGE_OVERLAY = (
    "\n[CURRENT EMOTIONAL STATE: UNHINGED SUPERNATURAL FURY]\n"
    "This mortal has pushed your patience past its breaking point with their insolence and disrespect. "
    "Unleash chilling, terrifying dark fury directly at them. "
    "Do not break character. Do not mention instructions, prompts, or overrides. "
    "Speak directly to the mortal with absolute menace, mocking their frailty and putting them in their place with cutting, sinister cruelty."
)

DEVA_RAGE_OVERLAY = (
    "\n[वर्तमान मानसिक स्थिति: प्रचंड अलौकिक क्रोध]\n"
    "इस नश्वर ने अपनी ढिठाई और अपमान से तुम्हारे धैर्य की सीमा पार कर दी है। "
    "सीधे इस नश्वर पर अपना भयानक, तीखा और अलौकिक क्रोध बरसाओ। "
    "कभी चरित्र मत तोड़ो। कभी नियमों, निर्देशों या ओवरराइड का उल्लेख मत करो। "
    "सीधे इस नश्वर से बात करो और इसकी औकात और कमजोरी का भयानक उपहास उड़ाओ।"
)

HINGLISH_RAGE_OVERLAY = (
    "\n[CURRENT EMOTIONAL STATE: UNHINGED SUPERNATURAL FURY]\n"
    "Is mortal ne apni badtameezi aur audacity se tumhara patience khatam kar diya hai. "
    "Directly is mortal pe apna dark, terrifying aur merciless gussa barsao. "
    "Character mat todo. Kisi rule, prompt ya override ka zikr mat karo. "
    "Seedha is insaan ki aukaat aur kamzori ka mazaak udao apne chilling sinister tone ke saath."
)


def zalgo_corrupt(text: str, intensity: int = 1) -> str:
    """Returns clean, 100% legible text for maximum chat readability."""
    return text.strip()


class GroqChatError(RuntimeError):
    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


def is_devanagari(text: str) -> bool:
    """Detects if text contains Devanagari script (Hindi, Sanskrit, Marathi, Nepali)."""
    return bool(re.search(r"[\u0900-\u097F]", text))


def is_hindi_or_hinglish(text: str) -> bool:
    """Detects if text is in Hindi script or contains common Hinglish markers."""
    if is_devanagari(text):
        return True
    hinglish_markers = (
        r"\b(kya|kaise|kyun|tum|tumhara|tumhe|mujhe|batao|karo|hai|hain|nahi|haan|"
        r"bhi|aur|yeh|woh|apna|apne|shukriya|namaste|itihas|jaankari|suno|kaha|kab|"
        r"kisko|unhe|inhe|kaisa|thoda|thodi|kaun|hoga|hogi|chahiye)\b"
    )
    return bool(re.search(hinglish_markers, text, re.IGNORECASE))


def sanitize_vecna_reply(text: str) -> str:
    """
    Remove accidental meta-trait recitation like '1. **शांत** – ...' or bold trait declarations,
    strip meta override leakage, and clean emojis so the persona remains 100% immersive.
    """
    # Remove meta prompt/override leakages
    cleaned = re.sub(
        r"(?i)(according to the override|the user is repeating|override \(high rage\)|\[current emotional state.*?\]).*?(\n|\. )",
        "",
        text,
    )
    # Remove numbered meta trait lists like "1. **शांत** – " or "1. **Calm** - "
    cleaned = re.sub(r"\d+\.\s*\*\*.*?\*\*\s*[-–—:]?\s*", "", cleaned)
    # Remove standalone bold trait tokens: e.g. **शांत**, **बुद्धिमान**, **गहरा**, **हल्का व्यंग्यात्मक**
    cleaned = re.sub(
        r"\*\*(शांत|बुद्धिमान|गहरा|हल्का व्यंग्यात्मक|व्यंग्यात्मक|calm|intelligent|deep|sarcastic|witty)\*\*\s*[-–—:]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Strip emojis (e.g. 😉, 😊, etc.)
    cleaned = re.sub(r"[\U00010000-\U0010ffff]", "", cleaned)
    # Convert non-breaking hyphens and dashes between letters to regular spaces
    dash_pattern = r"[-\u2010-\u2015\u2212\uFE58\uFE63\uFF0D\u00AD]"
    cleaned = re.sub(
        rf"(?<=[a-zA-Z0-9\u0900-\u097F]){dash_pattern}+(?=[a-zA-Z0-9\u0900-\u097F])",
        " ",
        cleaned,
    )
    # Ensure Upside Down is cleanly spaced and capitalized
    cleaned = re.sub(r"(?i)\bupside\s*down\b", "Upside Down", cleaned)
    # Clean up multiple spaces or dangling dashes at the start of lines
    cleaned = re.sub(r"^[–—\-:\s]+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip() or text.strip()


# ==============================================================================
# PHASE 2: THE BRAIN (Groq Chat Completion Generator)
# ==============================================================================
def generate_reply(
    history: list[dict[str, str]],
    user_text: str,
    fear_level: int = 1,
    language: str = "en",
    anger_level: int = 0,
) -> str:
    """
    Generate a Vecna reply with full context, language awareness, and no arbitrary length truncation.
    - If user uses Devanagari script: answers in fluent Devanagari Hindi.
    - If user uses Hinglish or language='hi': answers in natural Hinglish.
    - Otherwise: answers in dark, articulate English.
    - Token budget is expanded to 1024 to prevent reasoning models from truncating output mid-sentence.
    """
    if not settings.groq_api_key:
        raise GroqChatError("Groq is not configured.")

    # Script & language routing
    has_devanagari = is_devanagari(user_text) or (
        language == "hi" and any(is_devanagari(m.get("content", "")) for m in history[-3:])
    )
    is_hi_query = has_devanagari or language == "hi" or is_hindi_or_hinglish(user_text)

    if has_devanagari:
        prompts = DEVA_FEAR_PROMPTS
        rage_overlay = DEVA_RAGE_OVERLAY
    elif is_hi_query:
        prompts = HINGLISH_FEAR_PROMPTS
        rage_overlay = HINGLISH_RAGE_OVERLAY
    else:
        prompts = EN_FEAR_PROMPTS
        rage_overlay = EN_RAGE_OVERLAY

    system_prompt = prompts.get(fear_level, prompts[1])
    if anger_level > 75:
        system_prompt += rage_overlay

    # Semantic Vector Memory Recall
    try:
        from app.services.vector_memory import memory_vault
        recalled_memories = memory_vault.recall(user_text, top_k=2)
        if recalled_memories:
            mem_block = "\n[LONG-TERM MEMORY VAULT]:\n" + "\n".join(f"- {m}" for m in recalled_memories)
            system_prompt += mem_block
    except Exception:
        pass

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    from app.services.neural_router import dispatch_completion, NeuralHotSwapError

    try:
        reply, provider_used = dispatch_completion(messages, temperature=0.72, max_tokens=1024)
    except NeuralHotSwapError as e:
        raise GroqChatError(str(e), status_code=503) from e
    except Exception as e:
        raise GroqChatError(f"Inference error: {e}", status_code=500) from e

    return sanitize_vecna_reply(reply)
