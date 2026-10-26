import { useState } from "react";
import type { Hop } from "../types";

const STAGE_LABELS: Record<string, string> = {
  customer_channel: "Customer Channel",
  authentication: "Authentication",
  payment_api: "Payment API",
  payment_switch: "Payment Switch",
  payment_rail: "Payment Rail (Raast)",
  receiving_institution: "Receiving Institution",
  core_banking: "Core Banking",
  settlement_reconciliation: "Settlement Reconciliation",
};

const STATUS_LABEL: Record<string, string> = {
  ok: "OK",
  break: "BREAK",
  unknown: "NOT REACHED",
};

function formatTime(ts: string | null): string {
  if (!ts) return "—";
  return new Date(ts).toLocaleString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export function HopCard({ hop, isBreakHop }: { hop: Hop; isBreakHop: boolean }) {
  const [expanded, setExpanded] = useState(isBreakHop);

  return (
    <div className={`hop-card status-${hop.status}`} id={`hop-${hop.id}`}>
      <div className="hop-rail">
        <div className={`hop-dot status-${hop.status}`} />
        {hop.sequence < 8 && <div className={`hop-line status-${hop.status}`} />}
      </div>
      <div className="hop-body">
        <div className="hop-header" onClick={() => setExpanded((v) => !v)}>
          <span className="hop-seq">{hop.sequence}</span>
          <span className="hop-stage">{STAGE_LABELS[hop.stage] ?? hop.stage}</span>
          <span className={`badge badge-${hop.status}`}>{STATUS_LABEL[hop.status]}</span>
          <span className="hop-time">{formatTime(hop.started_at)}</span>
          <span className="hop-toggle">{expanded ? "−" : "+"}</span>
        </div>

        {hop.notes && <div className="hop-notes">{hop.notes}</div>}

        {expanded && hop.artifacts.length > 0 && (
          <div className="artifact-list">
            {hop.artifacts.map((a) => (
              <div key={a.id} className="artifact">
                <div className="artifact-meta">
                  <span className="artifact-source">{a.source}</span>
                  <span className="artifact-type">{a.artifact_type}</span>
                  <span className="artifact-time">{formatTime(a.timestamp)}</span>
                </div>
                <pre className="artifact-payload">{JSON.stringify(a.raw_payload, null, 2)}</pre>
              </div>
            ))}
          </div>
        )}

        {expanded && hop.artifacts.length === 0 && hop.status === "break" && (
          <div className="artifact-empty">
            No artifact found from the expected source(s) — this absence is the break signal.
          </div>
        )}
      </div>
    </div>
  );
}
