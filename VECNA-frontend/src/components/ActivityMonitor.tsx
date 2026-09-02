type AssistantState = "idle" | "listening" | "thinking" | "speaking" | "error";

type ActivityMonitorProps = {
  state: AssistantState;
  angerLevel?: number; // 0-100
  fearLevel?: 1 | 2 | 3;
  curseActive?: boolean;
};

const activityDetails: Record<AssistantState, { label: string; entries: string[] }> = {
  idle: {
    label: "HAWKINS SCANNING",
    entries: ["HNL RADAR GRID ARMED", "DEMOGORGON ACOUSTIC SILENT", "UPSIDE DOWN SPORES ACTIVE"],
  },
  listening: {
    label: "PSYCHIC CAPTURE",
    entries: ["VECNA TELEPATHIC SURGE", "ELECTROMAGNETIC FLUX", "TRACKING DEMOGORGON FREQ"],
  },
  thinking: {
    label: "RIFT RESONANCE",
    entries: ["UPSIDE DOWN CONVERGENCE", "VECNA IS TRANSCENDING", "CALIBRATING CLOCK TOWER"],
  },
  speaking: {
    label: "VOID BROADCAST",
    entries: ["TRANSMITTING THROUGH RIFT", "DEMOGORGON ROAR FILTERED", "AUDIO FREQ 14.8 kHz ARMED"],
  },
  error: {
    label: "CONTAINMENT BREACH",
    entries: ["SECTOR 4 RIFT UNSTABLE", "DEMOGORGON BREACH DETECTED", "RE-ESTABLISHING SHIELD"],
  },
};

function getRageLabel(level: number): string {
  if (level >= 90) return "CRITICAL FURY // UNHINGED";
  if (level >= 75) return "DARK RAGE ACTIVE";
  if (level >= 50) return "AGITATION RISING";
  if (level >= 25) return "MILD IRRITATION";
  return "CALM // PACIFIED";
}

function getFearLabel(level: 1 | 2 | 3): string {
  if (level === 3) return "STAGE III: VOID CONVERGENCE";
  if (level === 2) return "STAGE II: PSYCHIC REACH";
  return "STAGE I: SHADOW DORMANT";
}

export function ActivityMonitor({
  state,
  angerLevel = 0,
  fearLevel = 1,
  curseActive = false,
}: ActivityMonitorProps) {
  const activity = activityDetails[state];
  const isRaging = angerLevel > 75;

  const fearPct = fearLevel === 3 ? 100 : fearLevel === 2 ? 66 : 33;
  const fluxPct =
    state === "speaking" ? 95
    : state === "thinking" ? 80
    : state === "listening" ? 65
    : state === "error" ? 100
    : 25;

  return (
    <aside
      className={`activity-monitor state-${state} ${isRaging ? "raging" : ""} ${curseActive ? "curse-pulsing" : ""}`}
      aria-label="Vecna biometrics and emotional telemetry monitor"
    >
      <div className="monitor-heading">
        <span>HAWKINS BIOMETRICS</span>
        <i className={isRaging ? "indicator-raging" : ""} aria-hidden="true" />
      </div>

      <strong>{activity.label}</strong>

      <ol>
        {activity.entries.map((entry) => (
          <li key={entry}>{entry}</li>
        ))}
      </ol>

      {/* ── EMOTIONAL TELEMETRY BARS ── */}
      <div className="emotional-bars-hud">

        {/* Bar 1: RAGE / ANGER INDEX */}
        <div className="rage-bar-section" aria-label={`Rage index: ${angerLevel}%`}>
          <div className="rage-bar-header">
            <span className="rage-bar-label">⚡ RAGE INDEX</span>
            <span className={`rage-bar-pct ${isRaging ? "rage-critical" : ""}`}>
              {angerLevel}%
            </span>
          </div>
          <div className="rage-bar-track">
            <div
              className={`rage-bar-fill ${
                angerLevel >= 75 ? "rage-critical-fill"
                : angerLevel >= 50 ? "rage-high-fill"
                : angerLevel >= 25 ? "rage-mid-fill"
                : "rage-low-fill"
              }`}
              style={{ width: `${Math.max(4, angerLevel)}%` }}
            />
          </div>
          <span className={`rage-status-label ${isRaging ? "rage-status-alert" : ""}`}>
            {getRageLabel(angerLevel)}
          </span>
        </div>

        {/* Bar 2: FEAR / TERROR LEVEL */}
        <div className="telemetry-bar-row">
          <div className="telemetry-bar-header">
            <span>👁 TERROR LVL</span>
            <span>LVL {fearLevel}</span>
          </div>
          <div className="telemetry-bar-track">
            <div
              className={`telemetry-bar-fill fear-fill-lvl-${fearLevel}`}
              style={{ width: `${fearPct}%` }}
            />
          </div>
          <span className="telemetry-sublabel">{getFearLabel(fearLevel)}</span>
        </div>

        {/* Bar 3: RIFT RESONANCE FLUX */}
        <div className="telemetry-bar-row">
          <div className="telemetry-bar-header">
            <span>🌀 RIFT FLUX</span>
            <span>{fluxPct}%</span>
          </div>
          <div className="telemetry-bar-track">
            <div
              className={`telemetry-bar-fill flux-fill state-${state}`}
              style={{ width: `${fluxPct}%` }}
            />
          </div>
          <span className="telemetry-sublabel">
            {curseActive ? "⚡ CLOCK CURSE ACTIVE" : "ACOUSTIC SENSORS ONLINE"}
          </span>
        </div>

      </div>

      {isRaging && (
        <div className="rage-alert-banner" role="alert">
          ⚠ REPETITIVE QUERY OVERLOAD — DARK RAGE ACTIVE
        </div>
      )}

      <p className="panel-drag-hint">DOUBLE-CLICK OR HOLD TO DRAG</p>
    </aside>
  );
}
