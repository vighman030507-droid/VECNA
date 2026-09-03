import { LiveTelemetry } from "../api/nexusTools";

export type ComponentState = "ready" | "error" | "unknown" | "active";

export type StatusItem = { label: string; state: ComponentState; detail?: string };

type SystemStatusProps = {
  items: StatusItem[];
  telemetry?: LiveTelemetry | null;
};

const stateLabel: Record<ComponentState, string> = {
  ready: "READY",
  active: "ACTIVE",
  error: "ERROR",
  unknown: "UNCHECKED",
};

export function SystemStatus({ items, telemetry }: SystemStatusProps) {
  return (
    <aside className="system-status" aria-label="System status">
      <p className="status-title">SYSTEM STATUS // HAWKINS TELEMETRY</p>
      
      {telemetry && (
        <div className="telemetry-live-strip" style={{ marginBottom: "0.55rem", padding: "0.35rem 0.45rem", background: "rgba(10, 15, 30, 0.65)", border: "1px solid rgba(255, 45, 85, 0.3)", borderRadius: "4px", fontSize: "0.55rem", fontFamily: "'Share Tech Mono', monospace" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "3px" }}>
            <span style={{ color: "#ff88a3" }}>CPU: {telemetry.cpu_percent}%</span>
            <span style={{ color: "#00f2fe" }}>RAM: {telemetry.ram_used_gb}G / {telemetry.ram_total_gb}G ({telemetry.ram_percent}%)</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", color: "rgba(205, 230, 250, 0.75)" }}>
            <span>PWR: {telemetry.power_status}</span>
            <span>UPTIME: {telemetry.uptime}</span>
          </div>
        </div>
      )}

      <div className="status-grid">
        {items.map((item) => (
          <div className="status-tile" key={item.label}>
            <span className={`status-light ${item.state}`} title={stateLabel[item.state]} />
            <span className="status-tile-label">{item.label}</span>
            <strong>{item.detail ?? stateLabel[item.state]}</strong>
          </div>
        ))}
      </div>
      <p className="status-key"><i className="status-light ready" /> ready <i className="status-light error" /> error</p>
    </aside>
  );
}
