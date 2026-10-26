import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ConnectorStatus } from "../types";
import { ConnectorStatusBar } from "./ConnectorStatusBar";

describe("ConnectorStatusBar", () => {
  it("renders nothing when there are no statuses", () => {
    const { container } = render(<ConnectorStatusBar statuses={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders a pill per connector, named after it", () => {
    const statuses: ConnectorStatus[] = [
      { name: "raast_response", healthy: true, detail: null },
      { name: "switch_logs", healthy: false, detail: "timeout" },
    ];
    render(<ConnectorStatusBar statuses={statuses} />);

    expect(screen.getByText("raast_response")).toBeInTheDocument();
    expect(screen.getByText("switch_logs")).toBeInTheDocument();
  });

  it("marks a healthy connector's pill with the 'healthy' class and an unhealthy one with 'unhealthy'", () => {
    const statuses: ConnectorStatus[] = [
      { name: "raast_response", healthy: true, detail: null },
      { name: "switch_logs", healthy: false, detail: "timeout" },
    ];
    render(<ConnectorStatusBar statuses={statuses} />);

    expect(screen.getByText("raast_response").closest(".connector-pill")).toHaveClass("healthy");
    expect(screen.getByText("switch_logs").closest(".connector-pill")).toHaveClass("unhealthy");
  });
});
