import type { CSSProperties } from "react";

type AmbientHudProps = { active: boolean; level: number };

const signalBars = Array.from({ length: 28 }, (_, index) => {
  const normalizedIndex = index / 27;
  const curve = Math.sin(normalizedIndex * Math.PI);
  const baseHeight = 22 + curve * 64 + ((index * 19) % 34);
  return {
    x: 24 + index * 21.2,
    height: Math.round(baseHeight),
    delay: `${(index % 8) * -0.15}s`,
  };
});

export function AmbientHud({ active, level }: AmbientHudProps) {
  return (
    <div
      className={`ambient-hud ${active ? "is-active" : ""}`}
      style={{ "--audio-level": level } as CSSProperties}
      aria-hidden="true"
    >
      {/* Corner Tactical Telemetry Brackets with Hawkins Clearance Code */}
      <svg className="hud-brackets" viewBox="0 0 100 100" preserveAspectRatio="none">
        <path d="M 0,16 L 0,0 L 16,0" className="bracket-corner top-left" />
        <path d="M 84,0 L 100,0 L 100,16" className="bracket-corner top-right" />
        <path d="M 100,84 L 100,100 L 84,100" className="bracket-corner bottom-right" />
        <path d="M 16,100 L 0,100 L 0,84" className="bracket-corner bottom-left" />
      </svg>

      {/* Audio Spectrum Analyzer Waveform & Hawkins Threat Tracker */}
      <div className="signal-field-container">
        {/* Hawkins Lab Threat Banner */}
        <div className="hud-top-classification">
          <span className="hud-lab-stamp">HAWKINS LAB // DEPT OF ENERGY</span>
          <span className="hud-threat-level">THREAT LEVEL: DEMOGORGON SIGHTED</span>
        </div>

        <svg className="signal-field" viewBox="0 0 640 180" preserveAspectRatio="none">
          <defs>
            <linearGradient id="spectrumGradient" x1="0%" y1="100%" x2="0%" y2="0%">
              <stop offset="0%" stopColor="#00f2fe" stopOpacity="0.8" />
              <stop offset="60%" stopColor="#00f5d4" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#ff2252" stopOpacity="1" />
            </linearGradient>
            <linearGradient id="spectrumGradientActive" x1="0%" y1="100%" x2="0%" y2="0%">
              <stop offset="0%" stopColor="#ff1844" stopOpacity="0.9" />
              <stop offset="60%" stopColor="#ff3366" stopOpacity="1" />
              <stop offset="100%" stopColor="#00f5d4" stopOpacity="1" />
            </linearGradient>
          </defs>

          {/* Baseline Grid Line & Ticks */}
          <line className="signal-baseline" x1="18" y1="164" x2="622" y2="164" />
          {Array.from({ length: 15 }, (_, i) => (
            <line key={`tick-${i}`} className="signal-tick" x1={24 + i * 40} y1="164" x2={24 + i * 40} y2="170" />
          ))}

          {/* Audio Spectrum Bars */}
          {signalBars.map((bar, index) => (
            <line
              className="signal-line"
              key={bar.x}
              style={{ "--line-delay": bar.delay, "--bar-index": index } as CSSProperties}
              x1={bar.x}
              x2={bar.x}
              y1="162"
              y2={162 - bar.height}
            />
          ))}
        </svg>

        {/* HUD Telemetry Readout with Demogorgon Acoustic Radar */}
        <div className="hud-readout">
          <div className="hud-indicator-badge">
            <span className="hud-pulse-dot" />
            <p className="hud-caption">
              {active ? "DEMOGORGON ACOUSTIC // HUNTING" : "UPSIDE DOWN RADAR // MONITORING"}
            </p>
          </div>
          <span className="hud-meta">FREQ: 14.8 kHz // RIFT FLUX: CRITICAL</span>
        </div>
      </div>
    </div>
  );
}
