import type { ConnectorStatus } from "../types";

export function ConnectorStatusBar({ statuses }: { statuses: ConnectorStatus[] }) {
  if (statuses.length === 0) return null;
  return (
    <div className="connector-bar" title="Read-only connector health">
      {statuses.map((s) => (
        <span key={s.name} className={`connector-pill ${s.healthy ? "healthy" : "unhealthy"}`}>
          <span className="dot" />
          {s.name}
        </span>
      ))}
    </div>
  );
}
