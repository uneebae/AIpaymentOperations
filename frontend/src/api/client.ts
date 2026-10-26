import type { ConnectorStatus, DemoReference, InvestigationResult } from "../types";

const BASE = "/api";

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export function createInvestigation(reference: string, referenceType: string): Promise<InvestigationResult> {
  return fetch(`${BASE}/investigations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reference, reference_type: referenceType }),
  }).then((res) => asJson<InvestigationResult>(res));
}

export function listInvestigations(): Promise<InvestigationResult[]> {
  return fetch(`${BASE}/investigations`).then((res) => asJson<InvestigationResult[]>(res));
}

export function getConnectorStatus(): Promise<ConnectorStatus[]> {
  return fetch(`${BASE}/connectors/status`).then((res) => asJson<ConnectorStatus[]>(res));
}

export function getDemoReferences(): Promise<DemoReference[]> {
  return fetch(`${BASE}/demo/references`).then((res) => asJson<DemoReference[]>(res));
}

export function evidencePackUrl(investigationId: string, format: "json" | "pdf"): string {
  return `${BASE}/investigations/${investigationId}/evidence-pack.${format}`;
}
