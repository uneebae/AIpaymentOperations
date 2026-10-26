import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { RootCauseCandidate } from "../types";
import { RootCausePanel } from "./RootCausePanel";

describe("RootCausePanel", () => {
  it("shows a 'no break detected' message when there are no causes", () => {
    render(<RootCausePanel causes={[]} />);
    expect(screen.getByText(/no break detected/i)).toBeInTheDocument();
  });

  it("renders each candidate's label and confidence as a rounded percentage", () => {
    const causes: RootCauseCandidate[] = [
      { label: "Switch decline", confidence: 0.873, cited_hop_ids: ["hop-1"], pattern_id: "switch-decline" },
    ];
    render(<RootCausePanel causes={causes} />);

    expect(screen.getByText("Switch decline")).toBeInTheDocument();
    expect(screen.getByText("87%")).toBeInTheDocument();
    expect(screen.getByText("pattern: switch-decline")).toBeInTheDocument();
  });

  it("omits the pattern tag when pattern_id is null", () => {
    const causes: RootCauseCandidate[] = [
      { label: "Unclassified break", confidence: 0.3, cited_hop_ids: ["hop-1"], pattern_id: null },
    ];
    render(<RootCausePanel causes={causes} />);

    expect(screen.queryByText(/^pattern:/)).not.toBeInTheDocument();
  });

  it("scrolls to the cited hop element when its citation link is clicked", async () => {
    const user = userEvent.setup();
    const causes: RootCauseCandidate[] = [
      { label: "Switch decline", confidence: 0.9, cited_hop_ids: ["hop-42"], pattern_id: null },
    ];
    render(
      <>
        <div id="hop-hop-42" />
        <RootCausePanel causes={causes} />
      </>,
    );

    const scrollIntoView = vi.fn();
    document.getElementById("hop-hop-42")!.scrollIntoView = scrollIntoView;

    await user.click(screen.getByText(/view cited evidence/i));

    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "center" });
  });

  it("renders one citation link per cited hop id", () => {
    const causes: RootCauseCandidate[] = [
      { label: "Multi-hop cause", confidence: 0.5, cited_hop_ids: ["a", "b", "c"], pattern_id: null },
    ];
    render(<RootCausePanel causes={causes} />);

    expect(screen.getAllByText(/view cited evidence/i)).toHaveLength(3);
  });
});
