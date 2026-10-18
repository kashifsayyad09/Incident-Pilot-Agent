import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ConfidenceMeter, OptionBars } from "@/components/ui";

describe("ConfidenceMeter", () => {
  it("shows the model value unmodified and flags below-threshold", () => {
    render(<ConfidenceMeter value={0.4123} threshold={0.6} />);
    expect(screen.getByText("0.412")).toBeInTheDocument();
    expect(screen.getByText(/below threshold/)).toBeInTheDocument();
    expect(screen.getByRole("meter")).toHaveAttribute("aria-valuenow", "0.4123");
  });

  it("flags meets-threshold with text, not color alone", () => {
    render(<ConfidenceMeter value={0.9} threshold={0.6} />);
    expect(screen.getByText(/meets threshold/)).toBeInTheDocument();
  });

  it("renders an em dash, never a number, when no confidence was reported", () => {
    render(<ConfidenceMeter value={null} threshold={0.6} />);
    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.getByText("not reported")).toBeInTheDocument();
  });
});

describe("OptionBars", () => {
  it("marks the selected option and shows the model's probabilities", () => {
    render(
      <OptionBars options={["a", "b"]} probabilities={{ a: 0.25, b: 0.75 }} selected="b" />,
    );
    expect(screen.getByText("● b")).toBeInTheDocument();
    expect(screen.getByText("○ a")).toBeInTheDocument();
    expect(screen.getByText("0.750")).toBeInTheDocument();
  });

  it("shows an em dash for a missing probability instead of zero", () => {
    render(<OptionBars options={["a", "b"]} probabilities={{ a: 1 }} selected="a" />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
