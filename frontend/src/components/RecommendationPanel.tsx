import { evidencePackUrl } from "../api/client";

export function RecommendationPanel({
  recommendation,
  investigationId,
}: {
  recommendation: string;
  investigationId: string;
}) {
  return (
    <div className="card recommendation-card">
      <h2 className="card-title">Drafted Recommendation</h2>
      <p className="recommendation-disclaimer">
        Drafted for human review only — never auto-executed. No action is taken on this or any connected
        system.
      </p>
      <p className="recommendation-text">{recommendation}</p>
      <div className="evidence-actions">
        <a
          className="btn btn-secondary"
          href={evidencePackUrl(investigationId, "json")}
          target="_blank"
          rel="noreferrer"
        >
          Download evidence-pack.json
        </a>
        <a
          className="btn btn-secondary"
          href={evidencePackUrl(investigationId, "pdf")}
          target="_blank"
          rel="noreferrer"
        >
          Download evidence-pack.pdf
        </a>
      </div>
    </div>
  );
}
