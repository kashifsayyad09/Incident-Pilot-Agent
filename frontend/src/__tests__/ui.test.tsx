import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ModeBadge, SeverityPill, UnavailableBanner } from "@/components/ui";
import { TOOL_OPTIONS } from "@/lib/types";

describe("ui primitives", () => {
  it("labels simulation mode explicitly", () => {
    render(<ModeBadge mode="simulation" />);
    expect(screen.getByLabelText("Mode: simulation")).toBeInTheDocument();
  });

  it("labels live mode explicitly", () => {
    render(<ModeBadge mode="live" />);
    expect(screen.getByLabelText("Mode: live AWS")).toBeInTheDocument();
  });

  it("never conveys severity by color alone", () => {
    render(<SeverityPill severity="critical" />);
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
  });

  it("shows the unavailable reason", () => {
    render(<UnavailableBanner title="Down" reason="not configured" />);
    expect(screen.getByRole("status")).toHaveTextContent("not configured");
  });
});

describe("contract", () => {
  it("exposes the five typed decision options", () => {
    expect(TOOL_OPTIONS).toHaveLength(5);
  });
});
