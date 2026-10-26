import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  createInvestigation,
  evidencePackUrl,
  getConnectorStatus,
  getDemoReferences,
  listInvestigations,
} from "./client";

function mockFetchOnce(body: unknown, init: Partial<Response> = {}) {
  const response = {
    ok: true,
    status: 200,
    statusText: "OK",
    json: async () => body,
    text: async () => JSON.stringify(body),
    ...init,
  } as Response;
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
  return response;
}

describe("api client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("createInvestigation posts to /api/investigations with the reference payload", async () => {
    mockFetchOnce({ twin: { id: "abc" } });

    await createInvestigation("TXN123", "core_transaction_id");

    expect(fetch).toHaveBeenCalledWith(
      "/api/investigations",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reference: "TXN123", reference_type: "core_transaction_id" }),
      }),
    );
  });

  it("createInvestigation resolves with the parsed JSON body", async () => {
    mockFetchOnce({ twin: { id: "abc" }, explanation: "x" });

    const result = await createInvestigation("TXN123", "core_transaction_id");

    expect(result).toEqual({ twin: { id: "abc" }, explanation: "x" });
  });

  it("createInvestigation rejects with a descriptive error on a non-ok response", async () => {
    mockFetchOnce(
      {},
      { ok: false, status: 404, statusText: "Not Found", text: async () => "Investigation not found" },
    );

    await expect(createInvestigation("TXN123", "core_transaction_id")).rejects.toThrow(
      "404 Not Found: Investigation not found",
    );
  });

  it("listInvestigations calls GET /api/investigations", async () => {
    mockFetchOnce([]);

    await listInvestigations();

    expect(fetch).toHaveBeenCalledWith("/api/investigations");
  });

  it("getConnectorStatus calls GET /api/connectors/status", async () => {
    mockFetchOnce([{ name: "raast", healthy: true, detail: null }]);

    const result = await getConnectorStatus();

    expect(fetch).toHaveBeenCalledWith("/api/connectors/status");
    expect(result).toEqual([{ name: "raast", healthy: true, detail: null }]);
  });

  it("getDemoReferences calls GET /api/demo/references", async () => {
    mockFetchOnce([]);

    await getDemoReferences();

    expect(fetch).toHaveBeenCalledWith("/api/demo/references");
  });

  it("evidencePackUrl builds a json evidence-pack URL", () => {
    expect(evidencePackUrl("inv-1", "json")).toBe("/api/investigations/inv-1/evidence-pack.json");
  });

  it("evidencePackUrl builds a pdf evidence-pack URL", () => {
    expect(evidencePackUrl("inv-1", "pdf")).toBe("/api/investigations/inv-1/evidence-pack.pdf");
  });
});
