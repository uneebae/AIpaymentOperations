import { FormEvent, useState } from "react";
import type { DemoReference } from "../types";

interface Props {
  demoReferences: DemoReference[];
  loading: boolean;
  onInvestigate: (reference: string, referenceType: string) => void;
}

export function ReferenceSearch({ demoReferences, loading, onInvestigate }: Props) {
  const [reference, setReference] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    if (!reference.trim()) return;
    onInvestigate(reference.trim(), "core_transaction_id");
  }

  return (
    <div className="card search-card">
      <form onSubmit={submit} className="search-form">
        <input
          className="search-input"
          placeholder="Enter a transaction / rail reference, e.g. TXN2026082000123457"
          value={reference}
          onChange={(e) => setReference(e.target.value)}
        />
        <button className="btn btn-primary" type="submit" disabled={loading}>
          {loading ? "Investigating…" : "Investigate"}
        </button>
      </form>

      <div className="demo-chips">
        <span className="demo-chips-label">Try a seeded fixture reference:</span>
        {demoReferences.map((d) => (
          <button
            key={d.reference}
            type="button"
            className="chip"
            title={d.description}
            disabled={loading}
            onClick={() => onInvestigate(d.reference, d.reference_type)}
          >
            {d.label}
          </button>
        ))}
      </div>
    </div>
  );
}
