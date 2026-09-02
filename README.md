# 🕰️ VECNA // Stranger Things HUD Assistant

> **A Next-Generation AI Voice Assistant & Supernatural Upside Down HUD Interface**  
> *Conceptualized as an advanced J.A.R.V.I.S.-style conversational assistant, reborn under the dark, supernatural thematic wrapper of VECNA (Henry Creel / 001) from Stranger Things.*

---

## 👨‍💻 Developer & Author Information

* **Developer:** **Vighnesh Singh**
* **Academic Profile:** 2nd Year Undergraduate Student, **Automation & Robotics Engineering**
* **Institution:** Vivekanand Education Society's Institute of Technology (**VESIT**), Mumbai
* **Email:** [vighman030507@gmail.com](mailto:vighman030507@gmail.com)
* **Contact Number:** `+91 7304252207`

---

## ⚖️ Legal Disclaimers & Copyright Acknowledgements

* **J.A.R.V.I.S. (Iron Man / Marvel Cinematic Universe):**  
  The core assistant architecture, telemetry HUD concepts, system monitoring, and automated dispatch workflows are inspired by **J.A.R.V.I.S. (Just A Rather Very Intelligent System)** from *Iron Man* and *The Avengers*. All associated names, trademarks, and intellectual property belong to **Marvel Entertainment**, **Marvel Studios**, and **The Walt Disney Company**.

* **VECNA (Stranger Things / Netflix):**  
  The visual aesthetics, atmospheric soundscapes, audio prosody, persona prompts, grandfather clock motifs, and Upside Down lore are based on the character **Vecna (Henry Creel / One / 001)** created by the **Duffer Brothers** for *Stranger Things*. All associated titles, character names, imagery, and intellectual property belong to **Netflix, Inc.**

* **Educational & Research Fair Use Notice:**  
  This is an independent, non-commercial engineering project developed solely for academic research, pair-programming experimentation, artificial intelligence integration, and robotics interface design. No copyright infringement is intended.

---

## 🌌 System Architecture

```
JARVIS / VECNA
├── VECNA-backend/                  # High-Performance FastAPI Python 3.11 Backend
│   ├── app/
│   │   ├── api/                    # Modular REST endpoints: /chat, /speech, /web-actions, /local-actions
│   │   ├── services/               # Groq LLM Brain, Whisper STT, Pydub Demonic TTS, Anger & Repetition Engine
│   │   ├── schemas.py              # Pydantic v2 strict input/output contracts
│   │   ├── settings.py             # Typed configuration loaded from environment
│   │   └── main.py                 # FastAPI application factory with CORS middleware
│   ├── tests/                      # Automated test suite (22 unit & integration tests)
│   └── requirements.txt            # Python dependencies (FastAPI, uvicorn, edge-tts, pydub, groq)
│
└── VECNA-frontend/                 # Modern React 19 + TypeScript + Vite HUD Interface
    ├── src/
    │   ├── api/                    # Client connectors for Chat, Speech (STT/TTS), and System status
    │   ├── assets/                 # High-definition Upside Down loopable MP4s and audio samples
    │   ├── components/             # OrbControl, ActivityMonitor, SystemStatus, BriefingPanel, MovablePanel, CurseTimerWidget
    │   ├── three/                  # React Three Fiber 3D Canvas, audio-reactive embers, and post-processing
    │   ├── styles/                 # Cyberpunk & supernatural HUD styling, glassmorphism, responsive CSS
    │   └── App.tsx                 # Core application controller, hands-free wake word, VAD, and telemetry
    └── package.json                # Frontend toolchain dependencies (Three.js, Lucide, Vite)
```

---

## ⚡ Key Engineering Features

### 1. 🎙️ Hands-Free "Hello Vecna" Multi-Accent Wake-Word Detector
* **Continuous Background Listener:** Runs an unobtrusive Web Speech API background worker.
* **Accent Tolerance & Fuzzy Phonetic Matching:** Uses **Levenshtein edit-distance ($\le 2$)** alongside a phonetic regex engine scanning top-5 candidate hypotheses (`maxAlternatives: 5`). Reliably detects regional variations across Indian, British, American, and Australian English accents (`vecna`, `vekna`, `vigna`, `vikna`, `wackna`, `beckna`, `victor`, `vector`).
* **Sub-Bass Acoustic Cue:** Triggers an immediate $70\text{ Hz} \to 32\text{ Hz}$ sine-wave sub-bass pulse upon activation and transitions the HUD to psychic capture mode.
* **Safe Audio Handshake:** Gracefully releases the microphone stream with a backoff delay before `MediaRecorder` takes over.

### 2. 🔇 Silence Voice Activity Detection (VAD)
* **Real-time Spectral Analysis:** Real-time `AnalyserNode` monitoring at 60 FPS.
* **Auto-Cutoff:** Automatically terminates recording after $1.5\text{ seconds}$ of detected silence ($>90$ consecutive frames below threshold).
* **Zero-Click Pipeline:** Automatically packages the audio blob, submits it to `/api/transcribe`, and triggers conversational inference without requiring manual button clicks.

### 3. 🌐 Multilingual STT Audio Normalization (`/api/transcribe`)
* **16kHz Mono Resampling & Peak Normalization:** Converts incoming browser audio (`webm`, `ogg`, `wav`, `mp4`) to 16,000 Hz mono PCM with $0\text{ dBFS}$ peak gain normalization via Pydub before dispatching to Whisper.
* **Whisper Large v3 Turbo Integration:** Conditioned with prompt context for seamless Roman-script Hindi (Hinglish), pure Devanagari Hindi, and English.
* **Hallucination Suppression:** Automatically catches and purges empty audio buffers, background noise artifacts, and subtitle credits.

### 4. 🗣️ Demonic Dual-Voice Neural TTS Engine (`/api/tts`)
* **Intelligent Language Routing:**
  * **English (`en`):** `en-US-ChristopherNeural` (Deep, ominous baseline).
  * **Hindi / Hinglish (`hi`):** `hi-IN-MadhurNeural` (Natural cadence, fluent multilingual pronunciation).
  * **Fallback Chain:** Automatic fallback to `en-GB-RyanNeural` or `hi-IN-SwaraNeural` if primary synthesis fails.
* **Pydub Demonic Layering:**
  * **Primary Voice Track:** Boosted by `+3.0 dB` for vocal articulation.
  * **Shadow Track:** Ducked to `-16.0 dB`, filtered through a $2,500\text{ Hz}$ low-pass filter, and delayed by $20\text{ ms}$ (Haas stereo precedence effect) to simulate a dual-entity demonic resonance.
* **Dynamic Anger Prosody Modulation:**
  * When `angerLevel >= 50%`, the engine drops pitch to `-30 Hz` and accelerates delivery to `+5%` for an aggressive, unhinged delivery.
* **Compound Word Normalization:** Hyphens and non-breaking dashes in words like *"Upside Down"* are normalized to prevent letter-by-letter spelling glitches.

### 5. 🩸 3-Turn Escalating Fear & Repetition Anger Engine (`/api/chat`)
* **Bounded Turn Memory:** Tracks conversations across sessions with thread-safe history.
* **Ragebait & Lore Insecurity Scanner:** Scans queries for insults, challenges, and canon lore vulnerabilities (mentions of Eleven/011, Brenner, Henry Creel, defeats, physical taunts). Instantly spikes anger by $+35\%$ to $+45\%$.
* **Repetition Tracker:** Computes token similarity against the last 5 queries. Repetitive questions spike anger by $+35\%$ to $+40\%$, while unique questions decay anger by $-10\%$.
* **Escalation Stages:**
  * **Turn 1 (`fearLevel: 1`):** *Sarcastic Observer* — Fulfills queries with cynical wit.
  * **Turn 2 (`fearLevel: 2`):** *Threat State* — Generates a desktop `vecna_curse.txt` horror file and signals the local action dispatcher (`notepad`).
  * **Turn 3+ (`fearLevel: 3`):** *Void Convergence* — Triggers full Upside Down overdrive, red screen vignette contraction, and pulsing perimeter alerts.

### 6. 📊 Interactive HUD Telemetry & Biometrics
* **Full 3-Bar Biometric Telemetry:**
  * ⚡ **Rage / Anger Index (0–100%):** Transitions dynamically from calm dim-red to flashing neon-red with critical audio-visual alerts.
  * 👁 **Terror Escalation (Level 1–3):** Reflects psychic reach and stage progression.
  * 🌀 **Rift Flux Resonance:** Live acoustic and electromagnetic status monitor.
* **Central Voice Orb:** 180px circular video sphere (`Vecna.mp4`) with smooth audio-reactive pulsation.
* **Drag-and-Drop Safety Locks:** Movable HUD panels are locked against accidental clicks/drags. Requires a **double-click on the panel header** or a **500ms long-press** to unlock dragging.
* **3D Particle Canvas (React Three Fiber):** Live 3D ember and spore field scaling with fear level (250 → 600 particles), red atmospheric spotlights, and mouse-parallax camera movement.

---

## 🚀 Getting Started

### Prerequisites
* **Python 3.11+**
* **Node.js 20+** & **npm**
* **Groq API Key** (Free tier available at [console.groq.com](https://console.groq.com))
* **FFmpeg** installed on your system path (recommended for Pydub audio manipulation):
  ```bash
  # macOS (via Homebrew)
  brew install ffmpeg

  # Ubuntu/Debian
  sudo apt install ffmpeg

  # Windows (via Chocolatey or Scoop)
  choco install ffmpeg
  ```

---

### Step 1: Clone & Configure Backend

```bash
cd VECNA-backend

# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate       # On macOS/Linux
# .\.venv\Scripts\Activate.ps1  # On Windows

# 2. Install Python dependencies
pip install -r requirements.txt pytest httpx

# 3. Create .env file
cp .env.example .env
```

Edit `VECNA-backend/.env`:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_CHAT_MODEL=llama-3.3-70b-versatile
JARVIS_BACKEND_HOST=127.0.0.1
JARVIS_BACKEND_PORT=8765
JARVIS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
JARVIS_LOCAL_ACTIONS_ENABLED=false
```

Start the backend server:
```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload
```
* Backend health check: `http://127.0.0.1:8765/api/health`

---

### Step 2: Configure & Launch Frontend

In a new terminal:
```bash
cd VECNA-frontend

# 1. Install Node dependencies
npm install

# 2. Create .env file (if not present)
cat <<EOF > .env
VITE_DEMO_MODE=false
VITE_API_BASE_URL=http://127.0.0.1:8765/api
EOF

# 3. Start the Vite development server
npm run dev
```

Open your browser at **`http://localhost:5173`**.

---

## 🧪 Verification & Automated Testing

### Backend Test Suite
Run the 22-test automated suite covering chat, speech, STT, web actions, and local actions:
```bash
cd VECNA-backend
.venv/bin/python -m pytest tests/ -v
```

### Frontend Lint & Production Build
Validate TypeScript typings and build the distribution bundle:
```bash
cd VECNA-frontend
npm run lint
npm run build
```

---

## 📡 API Endpoint Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Backend liveness and readiness probe. |
| `POST` | `/api/chat` | Main conversational completion with 3-turn fear escalation, anger scoring, and Zalgo text corruption. |
| `GET` | `/api/voices` | Catalog of curated neural Edge-TTS voices. |
| `POST` | `/api/tts` | Synthesizes text to demonic dual-voice MP3 with Haas delay and anger prosody modulation. |
| `POST` | `/api/transcribe` | Pre-processes 16kHz mono audio and transcribes multilingual Hinglish/Hindi/English via Groq Whisper. |
| `POST` | `/api/web-actions/plan` | Generates verified URLs for YouTube, Spotify, Netflix, Prime Video, Hotstar, GitHub, etc. |
| `GET` | `/api/local-actions/status` | Reports OS bridge status for local desktop execution. |
| `POST` | `/api/local-actions/execute` | Launches allowlisted desktop utilities (e.g., Notepad, Calculator). |

---

## 📜 Credits & Attributions

* **Developer:** **Vighnesh Singh** (VESIT Mumbai — Automation & Robotics Engineering)
* **Design & Concept Inspiration:**
  * J.A.R.V.I.S. — Marvel Studios / The Walt Disney Company
  * Vecna / Stranger Things — Netflix / The Duffer Brothers
* **3D Community Assets:**
  * *Vecna – Fully Rigged* by Sketchfab creators ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/))
  * *Demogorgon IK Rig* ([CC0 Public Domain](https://creativecommons.org/publicdomain/zero/1.0/))

---

*“Your time is running out... But your code is clean.”* — **VECNA**
