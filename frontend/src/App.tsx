import { useEffect, useState } from "react";
import { createInvestigation, getConnectorStatus, getDemoReferences } from "./api/client";
import { ConnectorStatusBar } from "./components/ConnectorStatusBar";
import { ExplanationPanel } from "./components/ExplanationPanel";
import { RecommendationPanel } from "./components/RecommendationPanel";
import { ReferenceSearch } from "./components/ReferenceSearch";
import { RootCausePanel } from "./components/RootCausePanel";
import { ThemeToggle } from "./components/ThemeToggle";
import { Timeline } from "./components/Timeline";
import { useTheme } from "./hooks/useTheme";
import type { ConnectorStatus, DemoReference, InvestigationResult } from "./types";

export default function App() {
  const { theme, setTheme } = useTheme();
  const [demoReferences, setDemoReferences] = useState<DemoReference[]>([]);
  const [connectorStatuses, setConnectorStatuses] = useState<ConnectorStatus[]>([]);
  const [result, setResult] = useState<InvestigationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDemoReferences()
      .then(setDemoReferences)
      .catch(() => setDemoReferences([]));
    getConnectorStatus()
      .then(setConnectorStatuses)
      .catch(() => setConnectorStatuses([]));
  }, []);

  async function handleInvestigate(reference: string, referenceType: string) {
    setLoading(true);
    setError(null);
    try {
      const res = await createInvestigation(reference, referenceType);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Investigation failed");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-inner">
          <div>
            <h1>AI Payment Operations Engineer</h1>
            <p className="tagline">
              Deterministic correlation engine + AI reasoning layer for Raast P2P investigations
            </p>
          </div>
          <div className="app-header-controls">
            <ConnectorStatusBar statuses={connectorStatuses} />
            <ThemeToggle theme={theme} onChange={setTheme} />
          </div>
        </div>
      </header>

      <main className="app-main">
        <ReferenceSearch
          demoReferences={demoReferences}
          loading={loading}
          onInvestigate={handleInvestigate}
        />

        {error && <div className="card error-card">Error: {error}</div>}

        {result && (
          <>
            <div className="card twin-meta">
              <div>
                <span className="meta-label">Reference</span>
                <span className="meta-value">{result.twin.ref.reference}</span>
              </div>
              <div>
                <span className="meta-label">Investigation ID</span>
                <span className="meta-value mono">{result.twin.id}</span>
              </div>
              <div>
                <span className="meta-label">Correlation engine</span>
                <span className="meta-value mono">{result.twin.correlation_version}</span>
              </div>
              <div>
                <span className="meta-label">Overall status</span>
                <span
                  className={`meta-value status-text status-${result.twin.break_hop_id ? "break" : "ok"}`}
                >
                  {result.twin.break_hop_id ? "Break detected" : "Clean — no break"}
                </span>
              </div>
            </div>

            <div className="grid">
              <div className="grid-main">
                <Timeline twin={result.twin} />
              </div>
              <div className="grid-side">
                <ExplanationPanel
                  explanation={result.explanation}
                  modelVersion={result.model_version}
                  selfCorrected={result.self_corrected}
                />
                <RootCausePanel causes={result.root_causes} />
                <RecommendationPanel
                  recommendation={result.recommendation}
                  investigationId={result.twin.id}
                />
              </div>
            </div>
          </>
        )}

        {!result && !error && (
          <div className="empty-state">
            <p>Enter a reference above, or pick a seeded fixture to see a full investigation.</p>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <span>MVP scope: Raast P2P · one institution · five read-only connectors · no write actions.</span>
      </footer>
    </div>
  );
}
