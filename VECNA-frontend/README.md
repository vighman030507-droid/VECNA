# 👁️ VECNA Frontend Interface (`VECNA-frontend`)

> **Cyberpunk / Supernatural Upside Down HUD Interface**  
> *Developed by **Vighnesh Singh** (VESIT Mumbai — Automation & Robotics Engineering)*

---

## 👨‍💻 Author & Credits

* **Developer:** **Vighnesh Singh**
  * 2nd Year Undergraduate, Automation & Robotics Engineering
  * Vivekanand Education Society's Institute of Technology (**VESIT**), Mumbai
  * **Email:** [vighman030507@gmail.com](mailto:vighman030507@gmail.com) | **Contact:** `+91 7304252207`
* **Inspirations & Copyrights:**
  * **J.A.R.V.I.S.** holographic HUD and assistant mechanics inspired by *Iron Man* (Copyright © **Marvel Entertainment** / **Marvel Studios**).
  * **VECNA** theme, Upside Down visual language, and grandfather clock motifs from *Stranger Things* (Copyright © **Netflix** / **The Duffer Brothers**).
  * Built as a non-commercial educational project demonstrating real-time voice, 3D WebGL, and automation interfaces.

---

## ⚡ Key Frontend Features

### 1. 🎙️ Hands-Free "Hello Vecna" Multi-Accent Wake-Word Engine
* Continuous background listening via Web Speech API with automatic self-healing restart.
* **Accent Tolerance:** Evaluates top-5 hypothesis candidates (`maxAlternatives: 5`) using a **Levenshtein edit-distance ($\le 2$)** fuzzy matcher and phonetic regex to accommodate Indian, British, American, and Australian English accents.
* Activates immediately upon interim recognition results without waiting for speech completion.
* Plays an activation sub-bass tone ($70\text{ Hz} \to 32\text{ Hz}$) and transitions the HUD to psychic capture mode.

### 2. 🔇 Silence Voice Activity Detection (VAD)
* 60 FPS Web Audio `AnalyserNode` monitoring.
* Automatically cuts off microphone recording after $1.5\text{ seconds}$ of detected silence ($>90$ consecutive frames below threshold).
* Submits audio to `/api/transcribe` with the selected language context for hands-free conversational flow.

### 3. 📊 Full 3-Bar Hawkins Telemetry HUD
* **Activity Monitor (`ActivityMonitor.tsx`):**
  * ⚡ **RAGE / ANGER INDEX (0–100%):** Color-graded from dim red to pulsating critical neon red with rage alert banners when anger exceeds 75%.
  * 👁 **TERROR ESCALATION (Level 1–3):** Reflects psychic curse stage.
  * 🌀 **RIFT FLUX RESONANCE:** Live acoustic and electromagnetic status monitor.
* **Central Voice Orb (`OrbControl.tsx`):** Circular 180px glowing video sphere (`Vecna.mp4`) with smooth audio-reactive pulsation.
* **Drag-and-Drop Safety Locks (`MovablePanel.tsx`):** Panels are locked against accidental dragging. Requires either a **double-click on the header** or a **500ms long-press** to unlock.

### 4. 🌌 3D Supernatural WebGL Canvas (React Three Fiber)
* 3D ember and spore particle field scaling with `fearLevel` (250 → 600 particles).
* Red atmospheric spotlights, mouse-parallax camera movement, and audio-reactive mesh pulsation.

### 5. 🎬 Seamless Double-Buffered 1080p Video Backdrop
* Zero-gap, stutter-free crossfading video player delivering an immersive Upside Down loop.

---

## 🛠️ Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Configure environment (.env)
cat <<EOF > .env
VITE_DEMO_MODE=false
VITE_API_BASE_URL=http://127.0.0.1:8765/api
EOF

# 3. Start development server
npm run dev
```

Open your browser at **`http://localhost:5173`**.

---

## 🏗️ Development Scripts

```bash
npm run dev      # Start Vite dev server
npm run lint     # Run TypeScript typechecks (tsc --noEmit)
npm run build    # Compile production bundle
npm run preview  # Preview production bundle locally
```

---

## 📜 3D Asset Attribution

* **[Vecna – Fully Rigged](https://sketchfab.com/3d-models/vecna-fully-rigged-2ed1e61a360f4ac285614611ea698f72)** — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
* **[Demogorgon IK Rig](https://sketchfab.com/3d-models/demogorgon-ik-rig-read-description-bdbbfe5778eb4fe5ac3232a2d43597bb)** — CC0 / Public Domain
