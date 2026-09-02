# 🧠 VECNA Backend Engine (`VECNA-backend`)

> **FastAPI Intelligence Core for the VECNA Assistant**  
> *Developed by **Vighnesh Singh** (VESIT Mumbai — Automation & Robotics Engineering)*

---

## 👨‍💻 Author & Credits

* **Developer:** **Vighnesh Singh**
  * 2nd Year Undergraduate, Automation & Robotics Engineering
  * Vivekanand Education Society's Institute of Technology (**VESIT**), Mumbai
  * **Email:** [vighman030507@gmail.com](mailto:vighman030507@gmail.com) | **Contact:** `+91 7304252207`
* **Inspirations & Copyrights:**
  * **J.A.R.V.I.S.** architecture inspired by *Iron Man* (Copyright © **Marvel Entertainment** / **Marvel Studios**).
  * **VECNA** persona, lore, and aesthetic wrapped from *Stranger Things* (Copyright © **Netflix** / **The Duffer Brothers**).
  * Developed strictly as a non-commercial educational project for AI and robotics interfacing research.

---

## 🚀 Engine Architecture & Services

The backend is built with **FastAPI** (Python 3.11) and provides asynchronous, high-throughput endpoints for conversational AI, speech processing, and system automation.

```
app/
├── api/
│   ├── chat.py             # POST /api/chat — 3-turn fear escalation, anger scoring, Zalgo corruption
│   ├── speech.py           # POST /api/transcribe, POST /api/tts, GET /api/voices
│   ├── web_actions.py      # POST /api/web-actions/plan — Query-to-URL action planner
│   └── local_actions.py    # GET /status, POST /plan, POST /execute — OS bridge
├── services/
│   ├── anger_store.py      # Thread-safe session repetition tracker & lore ragebait scanner
│   ├── conversation.py     # LRU bounded conversation memory (6 turns / 12 messages)
│   ├── groq_chat.py        # Groq LLaMA-3.3 inference, multilingual persona prompts, anti-meta filters
│   ├── groq_stt.py         # 16kHz audio normalization & Whisper Large v3 Turbo transcription
│   ├── edge_tts_service.py # Neural Edge-TTS synthesis + Pydub demonic dual-track Haas delay
│   └── web_action_planner.py# Safe URL construction for streaming and media platforms
├── schemas.py              # Pydantic v2 data models with strict validation
├── settings.py             # Environment configuration loader
└── main.py                 # FastAPI application factory with CORS middleware
```

---

## ⚡ Core Capabilities

### 1. Multilingual STT Audio Pre-Processing (`/api/transcribe`)
* **16kHz Mono Resampling:** Resamples incoming browser audio to 16,000 Hz single-channel PCM.
* **Peak Gain Normalization:** Applies dynamic gain up to $0\text{ dBFS}$ peak to ensure Whisper receives clean amplitude regardless of mic sensitivity.
* **Whisper Large v3 Turbo:** Conditioned with language-specific prompts supporting Roman Hinglish, Devanagari Hindi, and English without phonetic degradation.

### 2. Demonic Dual-Voice Neural TTS Engine (`/api/tts`)
* **Voice Routing:**
  * English (`en`): `en-US-ChristopherNeural` (`pitch="-18Hz"`, `rate="-8%"`).
  * Hindi / Hinglish (`hi`): `hi-IN-MadhurNeural` (`pitch="-18Hz"`, `rate="-8%"`).
  * Fallback to `en-GB-RyanNeural` or `hi-IN-SwaraNeural` if primary synthesis fails.
* **Pydub Demonic Dual-Track Layering:**
  * Primary vocal track boosted by `+3.0 dB`.
  * Secondary shadow track ducked by `-16.0 dB`, filtered via a $2,500\text{ Hz}$ low-pass filter, and shifted by $20\text{ ms}$ (Haas delay).
* **Anger Modulation:**
  * When `angerLevel >= 50%`, the engine automatically drops pitch to `-30 Hz` and accelerates delivery to `+5%`.

### 3. Escalating Fear & Anger Engine (`/api/chat`)
* **Repetition Tracker:** Computes token similarity and exact phrase repeats against recent session history. Identical or semantically repetitive queries increase `angerLevel` by $+35\%$ to $+40\%$.
* **Ragebait Scanner:** Regex scanner detecting canon lore insecurities (Eleven, Brenner, Henry Creel, defeats) and insults, immediately triggering $+35\%$ to $+45\%$ anger spikes.
* **Fear Stages:**
  * **Turn 1 (`fearLevel: 1`):** *Sarcastic Observer* — Fulfills queries with cynical wit.
  * **Turn 2 (`fearLevel: 2`):** *Threat State* — Drops `vecna_curse.txt` on desktop and launches Notepad.
  * **Turn 3+ (`fearLevel: 3`):** *Void Convergence* — Overdrive mode with maximum hostility.

---

## 🛠️ Setup & Running

```bash
# 1. Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt pytest httpx

# 3. Configure environment
cp .env.example .env
# Ensure GROQ_API_KEY is populated

# 4. Start the server
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload
```

---

## 🧪 Testing

Run the automated test suite:
```bash
.venv/bin/python -m pytest tests/ -v
```
All 22 unit and integration tests validate the chat completion flow, voice catalog, STT pre-processing, web actions, and local bridge.
