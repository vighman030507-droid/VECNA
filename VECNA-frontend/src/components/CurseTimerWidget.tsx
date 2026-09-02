import { useEffect, useState } from "react";

type CurseTimerWidgetProps = {
  active: boolean;
  onExpire?: () => void;
  durationSeconds?: number;
};

export function CurseTimerWidget({
  active,
  onExpire,
  durationSeconds = 3,
}: CurseTimerWidgetProps) {
  const [secondsLeft, setSecondsLeft] = useState(durationSeconds);

  useEffect(() => {
    if (!active) {
      setSecondsLeft(durationSeconds);
      return;
    }
    setSecondsLeft(durationSeconds);
    const interval = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          if (onExpire) onExpire();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [active, durationSeconds, onExpire]);

  if (!active) return null;

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const formattedTime = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

  return (
    <div className="curse-timer-widget" role="alert" aria-live="assertive">
      <div className="curse-header">
        <span className="curse-clock-icon">🕰️</span>
        <span className="curse-title">VECNA CURSE ACTIVE</span>
      </div>
      <div className="curse-countdown">
        <span className="curse-digits">{formattedTime}</span>
        <span className="curse-label">UNTIL CONVERGENCE</span>
      </div>
      <div className="curse-status-bar">
        <div
          className="curse-progress-fill"
          style={{ width: `${((durationSeconds - secondsLeft) / durationSeconds) * 100}%` }}
        />
      </div>
      <p className="curse-warning">EVERY SECOND PULLS YOU DEEPER INTO THE UPSIDE DOWN</p>
    </div>
  );
}
