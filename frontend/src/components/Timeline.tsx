import type { TransactionDigitalTwin } from "../types";
import { HopCard } from "./HopCard";

export function Timeline({ twin }: { twin: TransactionDigitalTwin }) {
  return (
    <div className="card">
      <h2 className="card-title">Timeline</h2>
      <div className="timeline">
        {twin.hops.map((hop) => (
          <HopCard key={hop.id} hop={hop} isBreakHop={hop.id === twin.break_hop_id} />
        ))}
      </div>
    </div>
  );
}
