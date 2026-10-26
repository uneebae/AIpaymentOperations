import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { DemoReference } from "../types";
import { ReferenceSearch } from "./ReferenceSearch";

const DEMO_REFERENCES: DemoReference[] = [
  {
    reference: "TXN2026082000123456",
    reference_type: "core_transaction_id",
    label: "Clean transaction",
    description: "Fully successful transfer.",
  },
];

describe("ReferenceSearch", () => {
  it("submits the typed reference with reference_type core_transaction_id", async () => {
    const user = userEvent.setup();
    const onInvestigate = vi.fn();
    render(<ReferenceSearch demoReferences={[]} loading={false} onInvestigate={onInvestigate} />);

    await user.type(screen.getByPlaceholderText(/enter a transaction/i), "TXN999");
    await user.click(screen.getByRole("button", { name: /investigate/i }));

    expect(onInvestigate).toHaveBeenCalledWith("TXN999", "core_transaction_id");
  });

  it("does not submit when the input is empty or whitespace-only", async () => {
    const user = userEvent.setup();
    const onInvestigate = vi.fn();
    render(<ReferenceSearch demoReferences={[]} loading={false} onInvestigate={onInvestigate} />);

    await user.type(screen.getByPlaceholderText(/enter a transaction/i), "   ");
    await user.click(screen.getByRole("button", { name: /investigate/i }));

    expect(onInvestigate).not.toHaveBeenCalled();
  });

  it("trims leading/trailing whitespace from the submitted reference", async () => {
    const user = userEvent.setup();
    const onInvestigate = vi.fn();
    render(<ReferenceSearch demoReferences={[]} loading={false} onInvestigate={onInvestigate} />);

    await user.type(screen.getByPlaceholderText(/enter a transaction/i), "  TXN999  ");
    await user.click(screen.getByRole("button", { name: /investigate/i }));

    expect(onInvestigate).toHaveBeenCalledWith("TXN999", "core_transaction_id");
  });

  it("clicking a demo chip investigates it with its own reference_type", async () => {
    const user = userEvent.setup();
    const onInvestigate = vi.fn();
    render(
      <ReferenceSearch demoReferences={DEMO_REFERENCES} loading={false} onInvestigate={onInvestigate} />,
    );

    await user.click(screen.getByRole("button", { name: "Clean transaction" }));

    expect(onInvestigate).toHaveBeenCalledWith("TXN2026082000123456", "core_transaction_id");
  });

  it("disables the submit button and demo chips while loading", () => {
    render(<ReferenceSearch demoReferences={DEMO_REFERENCES} loading={true} onInvestigate={vi.fn()} />);

    expect(screen.getByRole("button", { name: /investigating/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Clean transaction" })).toBeDisabled();
  });
});
