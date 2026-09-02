import { useState, useEffect, useRef } from "react";
import { useProgress } from "@react-three/drei";
import gsap from "gsap";

export function LoadingGate({ onComplete }: { onComplete?: () => void }) {
  const { progress } = useProgress();
  const [typedLines, setTypedLines] = useState<string[]>([]);
  const [showSkip, setShowSkip] = useState(false);
  const [isRevealed, setIsRevealed] = useState(false);
  const gateRef = useRef<HTMLDivElement>(null);

  const lines = [
    "INITIALIZING UPSIDE DOWN LINK...",
    "CALIBRATING CLOCK TOWER FREQUENCY...",
    "VECNA COGNITIVE LINK ESTABLISHED.",
  ];

  // Typing effect
  useEffect(() => {
    let lineIdx = 0;
    const interval = setInterval(() => {
      if (lineIdx < lines.length) {
        setTypedLines((prev) => [...prev, lines[lineIdx]]);
        lineIdx++;
      } else {
        clearInterval(interval);
      }
    }, 600);

    // Show skip after 2s
    const skipTimer = setTimeout(() => setShowSkip(true), 2000);

    // Force finish max wait 4s
    const forceTimer = setTimeout(() => {
      handleComplete();
    }, 4000);

    return () => {
      clearInterval(interval);
      clearTimeout(skipTimer);
      clearTimeout(forceTimer);
    };
  }, []);

  // Complete when progress reaches 100%
  useEffect(() => {
    if (progress >= 100) {
      const timer = setTimeout(() => {
        handleComplete();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [progress]);

  function handleComplete() {
    if (isRevealed || !gateRef.current) return;
    setIsRevealed(true);

    gsap.to(gateRef.current, {
      opacity: 0,
      scale: 1.04,
      filter: "blur(12px)",
      duration: 0.85,
      ease: "power2.out",
      onComplete: () => {
        if (gateRef.current) {
          gateRef.current.style.display = "none";
        }
        onComplete?.();
      },
    });
  }

  // Keyboard shortcut: ESC to skip
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleComplete();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <div ref={gateRef} className="loading-gate" role="progressbar" aria-valuenow={Math.round(progress)}>
      <div className="gate-content">
        <div className="gate-brand">
          <span className="gate-glyph">☩</span>
          <h2>VECNA SYSTEM BOOT</h2>
        </div>

        <div className="gate-terminal">
          {typedLines.map((line, idx) => (
            <p key={idx} className="gate-line">
              <span className="gate-prompt">&gt;</span> {line}
            </p>
          ))}
          <span className="gate-cursor" />
        </div>

        <div className="gate-progress-wrap">
          <div className="gate-bar-track">
            <div className="gate-bar-fill" style={{ width: `${Math.max(progress, 15)}%` }} />
          </div>
          <div className="gate-progress-meta">
            <span>SYNC // {Math.round(Math.max(progress, 15))}%</span>
            <span>STATUS: TRANSCENDING</span>
          </div>
        </div>

        {showSkip && (
          <button type="button" className="gate-skip-btn" onClick={handleComplete}>
            ENTER IMMEDIATELY [ESC]
          </button>
        )}
      </div>
    </div>
  );
}
