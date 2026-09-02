import vecnaVideo from "../assets/Vecna.mp4";

type OrbState = "idle" | "listening" | "thinking" | "speaking" | "error";

type OrbControlProps = {
  disabled: boolean;
  onStart: () => void;
  onStop: () => void;
  state: OrbState;
};

export function OrbControl({ disabled, onStart, onStop, state }: OrbControlProps) {
  const label =
    state === "listening"
      ? "Release to send"
      : state === "thinking"
      ? "Processing request"
      : state === "speaking"
      ? "Vecna is responding"
      : "Hold to talk with Vecna";

  return (
    <button
      type="button"
      className={`orb-control state-${state}`}
      aria-label={label}
      disabled={disabled}
      onPointerDown={(event) => {
        event.currentTarget.setPointerCapture(event.pointerId);
        onStart();
      }}
      onPointerUp={onStop}
      onPointerCancel={onStop}
    >
      {/* Clean Loopable Vecna Video Core */}
      <span className="orb-video-mask" aria-hidden="true">
        <video
          className="orb-bg-video"
          autoPlay
          loop
          muted
          playsInline
          preload="auto"
        >
          <source src={vecnaVideo} type="video/mp4" />
        </video>
        <span className="orb-video-overlay" />
      </span>

      <span className="orb-status">
        {state === "listening"
          ? "LISTENING"
          : state === "thinking"
          ? "THINKING"
          : state === "speaking"
          ? "SPEAKING"
          : "HOLD TO TALK"}
      </span>
    </button>
  );
}
