import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { sendChatMessage } from "./api/chat";
import { fetchVoices, requestSpeech, transcribeRecording, Voice } from "./api/speech";
import { AmbientHud } from "./components/AmbientHud";
import { ActivityMonitor } from "./components/ActivityMonitor";
import { ComponentState, SystemStatus } from "./components/SystemStatus";
import { BriefingPanel } from "./components/BriefingPanel";
import { MovablePanel } from "./components/MovablePanel";
import { OrbControl } from "./components/OrbControl";
import { VecnaScene } from "./three/VecnaScene";
import { LoadingGate } from "./components/LoadingGate";
import { SeamlessVideoBackdrop } from "./components/SeamlessVideoBackdrop";
import { waitForBackend } from "./api/system";
import { isWebActionRequest, planWebAction, WebAction } from "./webActions";
import { executeLocalAction, getLocalActionStatus, isLocalActionRequest, LocalAction, planLocalAction } from "./localActions";
import { DEMO_MODE } from "./config/mode";
import { CurseTimerWidget } from "./components/CurseTimerWidget";
import { fetchLiveTelemetry, LiveTelemetry } from "./api/systemTools";
import backgroundVideo from "./assets/Futuristic_web_interface_backgro…_1080p_202609011655.mp4";

type Message = { author: "user" | "vecna"; text: string };
type Status = "idle" | "listening" | "thinking" | "speaking" | "error";
type WakeWordStatus = "listening" | "standby" | "triggered" | "unsupported" | "error";
type PendingAction =
  | { type: "web"; action: WebAction }
  | { type: "local"; action: LocalAction };

function defaultPanelPositions() {
  const viewportWidth = typeof window !== "undefined" ? window.innerWidth : 1440;
  const viewportHeight = typeof window !== "undefined" ? window.innerHeight : 900;
  const leftMargin = 32;
  return {
    activity: { x: leftMargin, y: 28 },
    status: { x: leftMargin, y: 310 },
    briefing: { x: leftMargin, y: 535 },
    orb: {
      x: Math.round((viewportWidth - 180) / 2),
      y: Math.max(60, Math.round((viewportHeight - 180) / 2 - 40)),
    },
    chat: {
      x: Math.max(340, viewportWidth - 424),
      y: Math.max(28, Math.round((viewportHeight - 560) / 2)),
    },
  };
}

export function App() {
  const [panelPositions, setPanelPositions] = useState(defaultPanelPositions);
  const sessionId = useRef(crypto.randomUUID());

  useEffect(() => {
    const handleResize = () => setPanelPositions(defaultPanelPositions());
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const animationRef = useRef<number | null>(null);
  const recordingStartedAtRef = useRef(0);
  const wakeWordRef = useRef<any>(null);
  const shouldWakeListenRef = useRef(true);
  const restartTimerRef = useRef<any>(null);
  const messagesRef = useRef<HTMLDivElement | null>(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const statusRef = useRef<Status>(status);
  statusRef.current = status;
  const [wakeWordStatus, setWakeWordStatus] = useState<WakeWordStatus>("standby");
  const [error, setError] = useState("");
  const [voices, setVoices] = useState<Voice[]>([]);
  const [voiceId, setVoiceId] = useState("en-US-ChristopherNeural");
  const [language, setLanguage] = useState<"en" | "hi">("en");
  const [level, setLevel] = useState(0);
  const [backendState, setBackendState] = useState<ComponentState>("unknown");
  const [backendStarting, setBackendStarting] = useState(!DEMO_MODE);
  const [microphoneState, setMicrophoneState] = useState<ComponentState>("unknown");
  const [sttState, setSttState] = useState<ComponentState>("unknown");
  const [ttsState, setTtsState] = useState<ComponentState>("unknown");
  const [chatState, setChatState] = useState<ComponentState>("unknown");
  const [localActionsState, setLocalActionsState] = useState<ComponentState>("unknown");
  const [localActionsEnabled, setLocalActionsEnabled] = useState(false);
  const [networkState, setNetworkState] = useState<ComponentState>(() => (navigator.onLine ? "ready" : "error"));
  const [bluetoothState] = useState<ComponentState>(() => ("bluetooth" in navigator ? "ready" : "unknown"));
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  const [fearLevel, setFearLevel] = useState<1 | 2 | 3>(1);
  const [curseActive, setCurseActive] = useState(false);
  const [angerLevel, setAngerLevel] = useState(0);
  const [telemetry, setTelemetry] = useState<LiveTelemetry | null>(null);

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      const data = await fetchLiveTelemetry();
      if (!cancelled && data) setTelemetry(data);
    };
    void poll();
    const interval = setInterval(poll, 3500);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      if (DEMO_MODE) {
        setBackendState("ready");
        setBackendStarting(false);
        setChatState("ready");
        setTtsState("ready");
        const items = await fetchVoices();
        if (!cancelled) {
          setVoices(items);
          setVoiceId(items[0]?.id ?? "demo-guy");
        }
        return;
      }

      const healthy = await waitForBackend();
      if (cancelled) return;
      setBackendState(healthy ? "ready" : "error");
      setBackendStarting(false);
      if (!healthy) {
        setError("Vecna backend did not start. Restart the app and try again.");
        return;
      }
      const voiceRequest = fetchVoices();
      const localActionsRequest = getLocalActionStatus();
      try {
        const items = await voiceRequest;
        if (cancelled) return;
        setVoices(items);
        if (!items.some((item) => item.id === voiceId)) setVoiceId(items[0]?.id ?? voiceId);
      } catch {
        if (!cancelled) setError("Voice options are unavailable. Text chat still works.");
      }
      try {
        const enabled = await localActionsRequest;
        if (cancelled) return;
        setLocalActionsEnabled(enabled);
        setLocalActionsState(enabled ? "ready" : "unknown");
      } catch {
        if (!cancelled) setLocalActionsState("error");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const updateNetwork = () => setNetworkState(navigator.onLine ? "ready" : "error");
    window.addEventListener("online", updateNetwork);
    window.addEventListener("offline", updateNetwork);
    return () => {
      window.removeEventListener("online", updateNetwork);
      window.removeEventListener("offline", updateNetwork);
    };
  }, []);

  // Play sub-bass activation sound effect
  const playActivationSound = useCallback(() => {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(70, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(32, ctx.currentTime + 0.45);
      gain.gain.setValueAtTime(0.55, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.45);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.45);
    } catch {
      // AudioContext unavailable or blocked
    }
  }, []);

  // Levenshtein edit distance for accent-tolerant phonetic matching
  const editDistance = (a: string, b: string): number => {
    const m = a.length, n = b.length;
    const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
    for (let i = 0; i <= m; i++) dp[i][0] = i;
    for (let j = 0; j <= n; j++) dp[0][j] = j;
    for (let i = 1; i <= m; i++) {
      for (let j = 1; j <= n; j++) {
        dp[i][j] = a[i - 1] === b[j - 1]
          ? dp[i - 1][j - 1]
          : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
      }
    }
    return dp[m][n];
  };

  // Detect wake phrase across English (US, UK, Indian, Aussie), Hindi, and acoustic approximations
  const isWakeWordTrigger = useCallback((transcript: string): boolean => {
    if (!transcript) return false;
    const clean = transcript.toLowerCase().replace(/[^a-z0-9\u0900-\u097F\s]/g, " ").trim();
    if (!clean) return false;

    // 1. Broad multi-accent phonetic regex
    // Covers variations: "hello/hey/hi/yo/ok" + "vecna/vekna/vegna/vigna/vikna/vickna/victor/vector/wackna/wekna/beckna/varna/vishna/vienna/vena"
    const multiAccentRegex = /(hello|hey|hi|ok|okay|wake up|yo|listen|sun|suno|alo|elo)?\s*(vecna|vekna|vigna|vikna|vickna|vegna|varna|wackna|beckna|victor|vector|vishna|vienna|vena|वेकना|वेक्ना|विग्ना|विकना)/i;
    if (multiAccentRegex.test(clean)) return true;

    // 2. Direct keyword contains
    if (
      clean.includes("vecna") ||
      clean.includes("vekna") ||
      clean.includes("vegna") ||
      clean.includes("vigna") ||
      clean.includes("vikna") ||
      clean.includes("wackna") ||
      clean.includes("beckna") ||
      clean.includes("वेकना") ||
      clean.includes("वेक्ना")
    ) {
      return true;
    }

    // 3. Word-level fuzzy distance check (handles heavy accents where Google maps to near-miss words)
    const words = clean.split(/\s+/).filter(Boolean);
    for (const w of words) {
      if (w.length >= 4) {
        if (editDistance(w, "vecna") <= 2 || editDistance(w, "vekna") <= 1) {
          return true;
        }
      }
    }

    return false;
  }, []);

  const startWakeWord = useCallback(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setWakeWordStatus("unsupported");
      return;
    }

    if (statusRef.current !== "idle" && statusRef.current !== "error") return;

    try {
      if (wakeWordRef.current) {
        try { wakeWordRef.current.abort(); } catch {}
        wakeWordRef.current = null;
      }

      shouldWakeListenRef.current = true;
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 5; // Scan top 5 candidate transcripts for accent tolerance

      // Use user's native English locale (e.g. en-IN, en-GB, en-US) for optimal acoustic model
      recognition.lang =
        language === "hi"
          ? "hi-IN"
          : navigator.language && navigator.language.toLowerCase().startsWith("en")
          ? navigator.language
          : "en-US";

      recognition.onstart = () => {
        setWakeWordStatus("listening");
      };

      recognition.onresult = (event: any) => {
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const res = event.results[i];
          for (let j = 0; j < res.length; j++) {
            const transcript = res[j].transcript;
            const lower = transcript.toLowerCase();

            // Voice Barge-in / Interrupt detection: stop speaking immediately if user interrupts
            if (statusRef.current === "speaking" && (
              lower.includes("stop") ||
              lower.includes("chup") ||
              lower.includes("ruko") ||
              lower.includes("quiet") ||
              lower.includes("shut up") ||
              lower.includes("shh") ||
              isWakeWordTrigger(transcript)
            )) {
              stopSpeech();
              setStatus("idle");
              return;
            }

            if (isWakeWordTrigger(transcript)) {
              shouldWakeListenRef.current = false;
              setWakeWordStatus("triggered");
              try { recognition.abort(); } catch {}
              wakeWordRef.current = null;

              playActivationSound();

              // 180ms delay gives browser time to release microphone before MediaRecorder requests it
              setTimeout(() => {
                void startListening();
              }, 180);
              return;
            }
          }
        }
      };

      recognition.onerror = (event: any) => {
        // 'no-speech' is normal silence timeout in Chrome — onend restarts it
        if (event.error === "no-speech") return;
        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
          setWakeWordStatus("error");
          shouldWakeListenRef.current = false;
        }
      };

      recognition.onend = () => {
        if (shouldWakeListenRef.current && (statusRef.current === "idle" || statusRef.current === "error")) {
          clearTimeout(restartTimerRef.current);
          restartTimerRef.current = setTimeout(() => {
            if (shouldWakeListenRef.current && (statusRef.current === "idle" || statusRef.current === "error")) {
              try {
                recognition.start();
              } catch {
                startWakeWord();
              }
            }
          }, 350);
        } else {
          setWakeWordStatus("standby");
        }
      };

      recognition.start();
      wakeWordRef.current = recognition;
      setWakeWordStatus("listening");
    } catch {
      wakeWordRef.current = null;
      setWakeWordStatus("standby");
    }
  }, [language, isWakeWordTrigger, playActivationSound]);

  const toggleWakeWord = useCallback(() => {
    if (wakeWordStatus === "listening") {
      shouldWakeListenRef.current = false;
      if (wakeWordRef.current) {
        try { wakeWordRef.current.abort(); } catch {}
        wakeWordRef.current = null;
      }
      setWakeWordStatus("standby");
    } else {
      startWakeWord();
    }
  }, [wakeWordStatus, startWakeWord]);

  // Manage hands-free wake word lifecycle (listening when idle/error/speaking for barge-in)
  useEffect(() => {
    if (status === "idle" || status === "error" || status === "speaking") {
      startWakeWord();
    } else {
      shouldWakeListenRef.current = false;
      if (wakeWordRef.current) {
        try { wakeWordRef.current.abort(); } catch {}
        wakeWordRef.current = null;
      }
      setWakeWordStatus("standby");
    }

    return () => {
      clearTimeout(restartTimerRef.current);
      if (wakeWordRef.current) {
        try { wakeWordRef.current.abort(); } catch {}
        wakeWordRef.current = null;
      }
    };
  }, [status, startWakeWord]);

  // Unlock background mic wake listener on first user interaction if blocked by browser policy
  useEffect(() => {
    const handleGesture = () => {
      if (wakeWordStatus === "standby" && (statusRef.current === "idle" || statusRef.current === "error")) {
        startWakeWord();
      }
    };
    window.addEventListener("pointerdown", handleGesture, { once: true });
    return () => window.removeEventListener("pointerdown", handleGesture);
  }, [wakeWordStatus, startWakeWord]);

  useEffect(() => () => {
    stopSpeech();
    stopCapture();
  }, []);

  // Unlock browser autoplay policy on the very first user interaction.
  // After this fires once, audio.play() will never throw NotAllowedError again.
  useEffect(() => {
    const unlock = () => {
      const silentAudio = new Audio();
      silentAudio.src = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=";
      void silentAudio.play().catch(() => {});
      document.removeEventListener("click", unlock, true);
      document.removeEventListener("keydown", unlock, true);
      document.removeEventListener("touchstart", unlock, true);
    };
    document.addEventListener("click", unlock, { capture: true, once: true });
    document.addEventListener("keydown", unlock, { capture: true, once: true });
    document.addEventListener("touchstart", unlock, { capture: true, once: true });
    return () => {
      document.removeEventListener("click", unlock, true);
      document.removeEventListener("keydown", unlock, true);
      document.removeEventListener("touchstart", unlock, true);
    };
  }, []);

  useEffect(() => {
    requestAnimationFrame(() => messagesRef.current?.scrollTo({ top: messagesRef.current.scrollHeight, behavior: "smooth" }));
  }, [messages, status, pendingAction]);

  function stopSpeech() {
    if (DEMO_MODE && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    audioRef.current?.pause();
    audioRef.current = null;
    if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
    audioUrlRef.current = null;
  }

  function stopCapture() {
    if (animationRef.current) cancelAnimationFrame(animationRef.current);
    animationRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    void audioContextRef.current?.close();
    audioContextRef.current = null;
    setLevel(0);
  }

  function speakWithBrowserSpeech(text: string) {
    if (!("speechSynthesis" in window)) {
      setStatus("idle");
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onstart = () => {
      setTtsState("ready");
      setStatus("speaking");
    };
    utterance.onend = () => {
      setStatus("idle");
    };
    utterance.onerror = () => {
      setStatus("idle");
    };
    window.speechSynthesis.speak(utterance);
  }

  async function playSpeech(text: string, anger: number = angerLevel) {
    if (!text || !text.trim()) {
      return;
    }
    if (DEMO_MODE) {
      speakWithBrowserSpeech(text);
      return;
    }
    try {
      stopSpeech();
      const isHindi = language === "hi" || /[\u0900-\u097F]/.test(text);
      const targetVoice = isHindi
        ? (voiceId.startsWith("hi-") ? voiceId : "hi-IN-MadhurNeural")
        : (voiceId || "en-US-ChristopherNeural");
      const targetLang = isHindi ? "hi" : language;
      const blob = await requestSpeech(text, targetVoice, targetLang, anger);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.volume = 1.0;
      audio.preload = "auto";
      audioRef.current = audio;
      audioUrlRef.current = url;

      // Animate visualizer smoothly while speaking
      let animId: number;
      const startTime = performance.now();
      const updateSpeakingMeter = () => {
        if (audio.paused || audio.ended) {
          setLevel(0);
          return;
        }
        const elapsed = (performance.now() - startTime) / 1000;
        const pulse = 0.55 + Math.sin(elapsed * 9) * 0.25 + Math.sin(elapsed * 17) * 0.15;
        setLevel(Math.min(1, Math.max(0.1, pulse)));
        animId = requestAnimationFrame(updateSpeakingMeter);
      };

      audio.onplay = () => {
        setStatus("speaking");
        animId = requestAnimationFrame(updateSpeakingMeter);
      };

      audio.onended = () => {
        if (audioUrlRef.current === url) URL.revokeObjectURL(url);
        cancelAnimationFrame(animId);
        setLevel(0);
        setStatus("idle");
      };

      audio.onerror = () => {
        if (audioUrlRef.current === url) URL.revokeObjectURL(url);
        cancelAnimationFrame(animId);
        setLevel(0);
        setStatus("idle");
      };

      setError("");
      setTtsState("ready");
      setStatus("speaking");

      try {
        await audio.play();
      } catch (playErr) {
        // NotAllowedError = browser autoplay policy: not a real failure,
        // audio is buffered and will play on the next user gesture.
        if (playErr instanceof Error && playErr.name === "NotAllowedError") {
          // Queue audio to play on next click anywhere
          const resume = () => {
            void audio.play().catch(() => {});
            document.removeEventListener("click", resume);
            document.removeEventListener("keydown", resume);
          };
          document.addEventListener("click", resume, { once: true });
          document.addEventListener("keydown", resume, { once: true });
          setStatus("idle");
          return;
        }
        // Any other error (e.g. network, decode) is a real failure
        throw playErr;
      }
    } catch (reason) {
      setTtsState("error");
      setError(reason instanceof Error ? reason.message : "Speech generation is unavailable. The text reply is still available.");
      setStatus("idle");
    }
  }

  async function askVecna(text: string) {
    stopSpeech();
    setError("");
    setPendingAction(null);
    setMessages((current) => [...current, { author: "user", text }]);

    const isDevanagari = /[\u0900-\u097F]/.test(text);
    const effectiveLang: "en" | "hi" = isDevanagari ? "hi" : language;
    if (isDevanagari && language !== "hi") {
      setLanguage("hi");
      setVoiceId("hi-IN-MadhurNeural");
    }

    if (DEMO_MODE) {
      if (isLocalActionRequest(text)) {
        const reply = "Local app actions will be connected to the backend on Day 2.";
        setMessages((current) => [...current, { author: "vecna", text: reply }]);
        setStatus("idle");
        void playSpeech(reply);
        return;
      }
      if (isWebActionRequest(text)) {
        const reply = "Web actions will be connected to the backend on Day 2.";
        setMessages((current) => [...current, { author: "vecna", text: reply }]);
        setStatus("idle");
        void playSpeech(reply);
        return;
      }
      setStatus("thinking");
      try {
        const result = await sendChatMessage(sessionId.current, text, effectiveLang);
        setChatState("ready");
        setMessages((current) => [...current, { author: "vecna", text: result.reply }]);
        void playSpeech(result.reply);
      } catch (reason) {
        setChatState("error");
        setError(reason instanceof Error ? reason.message : "Vecna could not process that message.");
        setStatus("error");
      }
      return;
    }

    if (isLocalActionRequest(text)) {
      setStatus("thinking");
      try {
        const localAction = await planLocalAction(text);
        setPendingAction({ type: "local", action: localAction });
        setStatus("idle");
      } catch (reason) {
        setLocalActionsState("error");
        setError(reason instanceof Error ? reason.message : "Vecna could not prepare that local application.");
        setStatus("error");
      }
      return;
    }

    if (isWebActionRequest(text)) {
      setStatus("thinking");
      try {
        const webAction = await planWebAction(text);
        setPendingAction({ type: "web", action: webAction });
        setStatus("idle");
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Vecna could not prepare that web action.");
        setStatus("error");
      }
      return;
    }

    setStatus("thinking");
    try {
      const result = await sendChatMessage(sessionId.current, text, effectiveLang);
      setChatState("ready");
      const newAnger = result.angerLevel !== undefined ? result.angerLevel : angerLevel;
      if (result.fearLevel) setFearLevel(result.fearLevel);
      if (result.curseActive !== undefined) setCurseActive(result.curseActive);
      setAngerLevel(newAnger);

      // Turn 2: Automatic local action execution
      if (result.fearLevel === 2 && localActionsEnabled) {
        try {
          void executeLocalAction("notepad");
        } catch {
          // ignore if non-Windows or disabled
        }
      }

      setMessages((current) => [
        ...current,
        { author: "vecna", text: result.corruptedReply || result.reply },
      ]);
      void playSpeech(result.reply, newAnger);
    } catch (reason) {
      setChatState("error");
      setError(reason instanceof Error ? reason.message : "Vecna could not process that message.");
      setStatus("error");
    }
  }

  async function confirmAction() {
    if (!pendingAction) return;
    const currentAction = pendingAction;
    setPendingAction(null);

    if (currentAction.type === "web") {
      window.open(currentAction.action.url, "_blank", "noopener,noreferrer");
      const reply = `Opening ${currentAction.action.label}.`;
      setMessages((current) => [...current, { author: "vecna", text: reply }]);
      setStatus("idle");
      void playSpeech(reply);
      return;
    }

    if (currentAction.type === "local") {
      setStatus("thinking");
      try {
        const result = await executeLocalAction(currentAction.action.appId);
        setMessages((current) => [...current, { author: "vecna", text: result.message }]);
        setLocalActionsState("ready");
        setStatus("idle");
        void playSpeech(result.message);
      } catch (reason) {
        setLocalActionsState("error");
        setError(reason instanceof Error ? reason.message : "Vecna could not open that local application.");
        setStatus("error");
      }
    }
  }

  function cancelAction() {
    setPendingAction(null);
    const reply = "Action cancelled.";
    setMessages((current) => [...current, { author: "vecna", text: reply }]);
    setStatus("idle");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = input.trim();
    if (!text || status === "thinking" || backendStarting) return;
    setInput("");
    await askVecna(text);
  }

  async function startListening() {
    if (status === "thinking" || backendStarting || recorderRef.current) return;
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setError("This browser does not support microphone recording. Text chat remains available.");
      return;
    }
    try {
      setError("");
      stopSpeech();
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      streamRef.current = stream;
      setMicrophoneState("ready");
      const context = new AudioContext();
      audioContextRef.current = context;
      const analyser = context.createAnalyser();
      analyser.fftSize = 256;
      context.createMediaStreamSource(stream).connect(analyser);
      const samples = new Uint8Array(analyser.fftSize);
      let silenceFrames = 0;
      const updateMeter = () => {
        analyser.getByteTimeDomainData(samples);
        const mean = samples.reduce((sum, sample) => sum + Math.abs(sample - 128), 0) / samples.length;
        setLevel(Math.min(1, mean / 26));

        // Voice Activity Detection (VAD): auto-stop recording after ~1.5s of silence (90 frames at 60fps)
        if (mean < 2.5) {
          silenceFrames++;
          if (silenceFrames > 90 && recorderRef.current?.state === "recording") {
            const duration = performance.now() - recordingStartedAtRef.current;
            if (duration > 1500) { // Ensure minimum recording length
              finishListening();
            }
          }
        } else {
          silenceFrames = 0;
        }

        animationRef.current = requestAnimationFrame(updateMeter);
      };
      updateMeter();
      const chunks: BlobPart[] = [];
      // Prefer formats Groq Whisper handles best — no codec suffix in MIME to avoid fragmentation
      const preferredTypes = [
        "audio/webm",
        "audio/mp4",
        "audio/ogg",
        "audio/wav",
      ];
      const selectedMime = preferredTypes.find((t) => MediaRecorder.isTypeSupported(t)) ||
        (MediaRecorder.isTypeSupported("audio/webm;codecs=opus") ? "audio/webm;codecs=opus" : "");
      const recorder = selectedMime ? new MediaRecorder(stream, { mimeType: selectedMime }) : new MediaRecorder(stream);
      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) chunks.push(event.data);
      };
      recorder.onstop = () => {
        recorderRef.current = null;
        const duration = performance.now() - recordingStartedAtRef.current;
        stopCapture();
        if (duration < 650) {
          setError("Recording was too short. Hold the button while speaking, then release.");
          setSttState("error");
          setStatus("error");
          return;
        }

        if (DEMO_MODE) {
          const demoNotice = "Voice transcription will be connected on Day 2.";
          setMessages((current) => [
            ...current,
            { author: "vecna", text: demoNotice },
          ]);
          setSttState("ready");
          setStatus("idle");
          void playSpeech(demoNotice);
          return;
        }

        void (async () => {
          try {
            // Determine base MIME type — strip codec suffix so file extension maps cleanly
            const baseMime = (recorder.mimeType || selectedMime || "audio/webm").split(";")[0];
            const recordedBlob = new Blob(chunks, { type: baseMime });
            if (recordedBlob.size < 1200) {
              setSttState("ready");
              setStatus("idle");
              return;
            }

            setStatus("thinking");
            const transcript = await transcribeRecording(recordedBlob, language);
            if (!transcript || !transcript.trim()) {
              setSttState("ready");
              setStatus("idle");
              return;
            }
            setSttState("ready");
            setError("");
            await askVecna(transcript);
          } catch (reason) {
            setSttState("error");
            setError(reason instanceof Error ? reason.message : "Vecna could not transcribe that recording.");
            setStatus("error");
          }
        })();
      };
      // Do NOT timeslice (no argument to start()) — timesliced WebM produces fragmented
      // cluster blobs without EBML headers that Groq Whisper cannot parse.
      // We collect data only when stop() fires, giving us one complete valid audio file.
      recorder.start();
      recordingStartedAtRef.current = performance.now();
      setStatus("listening");
    } catch (reason) {
      stopCapture();
      setMicrophoneState("error");
      setError(
        reason instanceof Error && reason.name === "NotAllowedError"
          ? "Microphone permission was denied. Text chat remains available."
          : "Vecna could not access the microphone."
      );
      setStatus("error");
    }
  }

  function finishListening() {
    // Call stop() directly — the ondataavailable callback fires with the complete
    // recording blob right before onstop fires.
    if (recorderRef.current?.state === "recording") {
      recorderRef.current.stop();
    }
  }

  const active = status === "listening" || status === "thinking" || status === "speaking";
  const stateLabel = backendStarting
    ? "STARTING LOCAL BACKEND"
    : status === "listening"
    ? "LISTENING / HOLD TO TALK"
    : status === "thinking"
    ? "PROCESSING REQUEST"
    : status === "speaking"
    ? "VOICE OUTPUT ACTIVE"
    : "SYSTEM ONLINE";

  const statusItems = [
    { label: "HAWKINS NET", state: backendState, detail: DEMO_MODE ? "DEMO MODE" : backendState === "ready" ? "ONLINE" : undefined },
    { label: "RIFT GRID", state: networkState, detail: networkState === "ready" ? "ONLINE" : "OFFLINE" },
    { label: "VECNA CORE", state: chatState },
    { label: "DEMOGORGON", state: bluetoothState, detail: "TRACKING" },
    { label: "SPORE SENSOR", state: microphoneState },
    { label: "SPEECH TO TEXT", state: sttState },
    { label: "TEXT TO SPEECH", state: ttsState },
    { label: "CONTAINMENT", state: localActionsState, detail: DEMO_MODE ? "DAY 2" : localActionsEnabled ? "READY" : "DISABLED" },
  ];

  return (
    <main className={`app-shell ${curseActive ? "curse-active" : ""}`}>
      <LoadingGate />
      <CurseTimerWidget active={curseActive} onExpire={() => setCurseActive(false)} />

      {/* Layer 1: Seamless Double-Buffered Loopable Video Backdrop (z-index: 0) */}
      <SeamlessVideoBackdrop
        src="/backgrounds/vecna_loop.mp4"
        fallbackSrc={backgroundVideo}
        active={active}
        crossfadeDuration={0.8}
      />

      {/* Layer 2: Subtle Edge Vignette (z-index: 10, No scanlines/noise) */}
      <div className={`vignette-scanline-overlay ${curseActive ? "vignette-curse" : ""}`} aria-hidden="true" />

      {/* Layer 3: WebGL 3D Canvas Layer (z-index: 20) */}
      <VecnaScene
        status={status}
        level={status === "listening" ? level : status === "speaking" ? 0.72 : 0.25}
        fearLevel={fearLevel}
        curseActive={curseActive}
      />

      {/* Layer 4: Interactive Telemetry HUD Layer (z-index: 25 - 30) */}
      <AmbientHud active={active} level={status === "listening" ? level : status === "speaking" ? 0.72 : 0.35} />
      <MovablePanel id="orb" label="Vecna voice orb" className="orb-panel" defaultPosition={panelPositions.orb}>
        <OrbControl
          disabled={status === "thinking" || backendStarting}
          state={status}
          onStart={() => void startListening()}
          onStop={finishListening}
        />
      </MovablePanel>
      <MovablePanel id="activity" label="Activity monitor" className="activity-panel" defaultPosition={panelPositions.activity}>
        <ActivityMonitor
          state={status}
          angerLevel={angerLevel}
          fearLevel={fearLevel}
          curseActive={curseActive}
        />
      </MovablePanel>
      <MovablePanel id="system-status" label="System status" className="status-panel" defaultPosition={panelPositions.status}>
        <SystemStatus items={statusItems} telemetry={telemetry} />
      </MovablePanel>
      <MovablePanel id="briefing" label="Local system briefing" className="briefing-panel-wrapper" defaultPosition={panelPositions.briefing}>
        <BriefingPanel />
      </MovablePanel>
      <MovablePanel id="conversation" label="Vecna conversation" className="chat-panel" defaultPosition={panelPositions.chat}>
        <section className="chat-card" aria-label="Vecna assistant">
          <p className="vecna-brand">VECNA</p>
          <h1>{curseActive ? "CONTAINMENT BREACHED." : "OBSERVING FRAIL MORTALS."}</h1>
          <p className="connection-state">{stateLabel}</p>
          <div className="messages" ref={messagesRef} aria-live="polite">
            {messages.length === 0 && !pendingAction && <p>Type a message or hold to talk.</p>}
            {messages.map((message, index) => (
              <p className={`message ${message.author}`} key={`${message.author}-${index}`}>
                {message.text}
              </p>
            ))}
            {status === "thinking" && <p className="message vecna">Thinking…</p>}
            {pendingAction && (
              <div className="web-action-confirmation" role="alert">
                {pendingAction.type === "web" ? (
                  <>
                    <p>Open {pendingAction.action.label}?</p>
                    <small>{pendingAction.action.url}</small>
                  </>
                ) : (
                  <>
                    <p>Launch {pendingAction.action.label}?</p>
                    <small>Target: {pendingAction.action.appId}</small>
                  </>
                )}
                <div>
                  <button type="button" onClick={() => void confirmAction()}>
                    Confirm
                  </button>
                  <button type="button" onClick={cancelAction}>
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
          <button
            className={`talk-button ${status === "listening" ? "is-listening" : ""}`}
            type="button"
            onPointerDown={(event) => {
              event.currentTarget.setPointerCapture(event.pointerId);
              void startListening();
            }}
            onPointerUp={finishListening}
            onPointerCancel={finishListening}
            disabled={status === "thinking" || backendStarting}
          >
            {status === "listening" ? "Release to send" : backendStarting ? "Starting Vecna…" : "Hold to talk"}
          </button>
          <form onSubmit={handleSubmit} noValidate className="composer">
            <label className="sr-only" htmlFor="chat-input">
              Message Vecna
            </label>
            <input
              id="chat-input"
              value={input}
              maxLength={2000}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Message Vecna or hold to talk…"
              disabled={status === "thinking" || backendStarting}
            />
            <button type="submit" disabled={!input.trim() || status === "thinking" || backendStarting}>
              Send
            </button>
          </form>
          <label className="voice-picker" htmlFor="voice-select">
            Voice
            <select id="voice-select" value={voiceId} onChange={(event) => setVoiceId(event.target.value)} disabled={!voices.length}>
              {voices.map((voice) => (
                <option key={voice.id} value={voice.id}>
                  {voice.label}
                </option>
              ))}
            </select>
          </label>
          <label className="voice-picker lang-picker" htmlFor="lang-select">
            Language
            <select
              id="lang-select"
              value={language}
              onChange={(event) => {
                const lang = event.target.value as "en" | "hi";
                setLanguage(lang);
                // Auto-switch voice to language default when toggling
                if (lang === "hi" && !voiceId.startsWith("hi-")) setVoiceId("hi-IN-MadhurNeural");
                if (lang === "en" && voiceId.startsWith("hi-")) setVoiceId("en-US-ChristopherNeural");
              }}
            >
              <option value="en">🔊 English</option>
              <option value="hi">🔊 Hindi / Hinglish</option>
            </select>
          </label>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </section>
      </MovablePanel>
    </main>
  );
}
