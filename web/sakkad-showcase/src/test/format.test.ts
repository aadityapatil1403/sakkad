import { describe, it, expect } from "vitest";
import {
  sortedTaxonomy,
  topTaxonomyLabel,
  formatScore,
  formatDate,
  aggregateGroupTaxonomy,
} from "../lib/format";
import { mockCapture, mockAbstractCapture } from "./fixtures";

describe("sortedTaxonomy", () => {
  it("returns entries sorted by score descending", () => {
    const result = sortedTaxonomy({ Gorpcore: 0.12, "Quiet Luxury": 0.87 });
    expect(result[0]).toEqual(["Quiet Luxury", 0.87]);
    expect(result[1]).toEqual(["Gorpcore", 0.12]);
  });

  it("returns empty array for empty object", () => {
    expect(sortedTaxonomy({})).toEqual([]);
  });
});

describe("topTaxonomyLabel", () => {
  it("returns the highest scoring label", () => {
    expect(topTaxonomyLabel(mockCapture.taxonomy_matches)).toBe("Quiet Luxury");
  });

  it("returns null for empty matches", () => {
    expect(topTaxonomyLabel({})).toBeNull();
  });
});

describe("formatScore", () => {
  it("formats score as percentage string", () => {
    expect(formatScore(0.87)).toBe("87%");
    expect(formatScore(0.123)).toBe("12%");
  });

  it("handles null gracefully", () => {
    expect(formatScore(null)).toBe("—");
  });
});

describe("formatDate", () => {
  it("formats ISO date to readable string", () => {
    const result = formatDate("2026-04-24T10:00:00Z");
    expect(result).toContain("2026");
  });

  it("handles invalid date gracefully", () => {
    expect(formatDate("not-a-date")).toBe("—");
  });

  it("handles null gracefully", () => {
    expect(formatDate(null)).toBe("—");
  });
});

describe("aggregateGroupTaxonomy", () => {
  it("merges taxonomy_matches across captures, taking max score per label", () => {
    const captures = [mockCapture, mockAbstractCapture];
    const result = aggregateGroupTaxonomy(captures);
    expect(result["Quiet Luxury"]).toBe(0.87);
    expect(result["Concrete Brutalism"]).toBe(0.91);
  });

  it("includes abstract visual labels alongside fashion labels", () => {
    const result = aggregateGroupTaxonomy([mockAbstractCapture]);
    expect("Concrete Brutalism" in result).toBe(true);
    expect("Oxidized Metal" in result).toBe(true);
  });

  it("returns empty object for empty input", () => {
    expect(aggregateGroupTaxonomy([])).toEqual({});
  });
});
