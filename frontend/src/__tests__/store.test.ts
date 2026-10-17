import { describe, expect, it } from "vitest";
import { getIncidentState, selectIncident } from "@/lib/incidentStore";
import type { IncidentSummary } from "@/lib/types";

const inc: IncidentSummary = {
  id: "x",
  title: "t",
  summary: "s",
  category: "c",
  severity: "critical",
  affected_services: ["alb", "cloudwatch"],
  mode: "simulation",
};

describe("incident store", () => {
  it("flags only the services the scenario names and never claims others are healthy", () => {
    selectIncident(inc);
    const { scene } = getIncidentState();
    expect(scene.alb).toBe("critical");
    expect(scene.cloudwatch).toBe("critical");
    expect(scene.ec2).toBe("none");
    expect(scene.rds).toBe("none");
  });

  it("clears flags when nothing is selected", () => {
    selectIncident(null);
    expect(getIncidentState().scene.alb).toBe("none");
  });
});
