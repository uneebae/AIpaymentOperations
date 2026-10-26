import type { RootCauseCandidate } from "../types";

function scrollToHop(hopId: string) {
  document.getElementById(`hop-${hopId}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
}

export function RootCausePanel({ causes }: { causes: RootCauseCandidate[] }) {
  return (
    <div className="card">
      <h2 className="card-title">Root Cause Candidates</h2>
      {causes.length === 0 ? (
        <p className="muted">No break detected — nothing to classify.</p>
      ) : (
        <ul className="cause-list">
          {causes.map((c, i) => (
            <li key={i} className="cause-item">
              <div className="cause-row">
                <span className="cause-label">{c.label}</span>
                <span className="cause-confidence">{Math.round(c.confidence * 100)}%</span>
              </div>
              <div className="confidence-bar">
                <div className="confidence-fill" style={{ width: `${Math.round(c.confidence * 100)}%` }} />
              </div>
              <div className="cause-meta">
                {c.pattern_id && <span className="pattern-tag">pattern: {c.pattern_id}</span>}
                {c.cited_hop_ids.map((hid) => (
                  <button key={hid} className="cite-link" onClick={() => scrollToHop(hid)}>
                    view cited evidence →
                  </button>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
