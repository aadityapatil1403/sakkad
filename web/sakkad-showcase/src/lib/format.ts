import type { BackendCapture } from "./types";
export { isAbstractCapture } from "./types";

export function sortedTaxonomy(
  matches: Record<string, number>,
): [string, number][] {
  return Object.entries(matches).sort(([, a], [, b]) => b - a);
}

export function topTaxonomyLabel(
  matches: Record<string, number>,
): string | null {
  const top = sortedTaxonomy(matches)[0];
  return top ? top[0] : null;
}

export function formatScore(score: number | null): string {
  if (score === null || score === undefined) return "—";
  return `${Math.floor(score * 100)}%`;
}

export function formatDate(date: string | null): string {
  if (!date) return "—";
  const d = new Date(date);
  if (isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function aggregateGroupTaxonomy(
  captures: BackendCapture[],
): Record<string, number> {
  const result: Record<string, number> = {};
  for (const capture of captures) {
    for (const [label, score] of Object.entries(capture.taxonomy_matches)) {
      result[label] = Math.max(result[label] ?? 0, score);
    }
  }
  return result;
}

export function aggregateGroupTags(captures: BackendCapture[]): {
  layer1: string[];
  layer2: string[];
  references: string[];
} {
  const layer1 = new Set<string>();
  const layer2 = new Set<string>();
  const references = new Set<string>();

  for (const c of captures) {
    for (const t of c.layer1_tags ?? []) layer1.add(t);
    for (const t of c.layer2_tags ?? []) layer2.add(t);
    for (const r of c.reference_matches ?? []) {
      if (r.score >= 0.15) references.add(`${r.brand} — ${r.title}`);
    }
  }

  return {
    layer1: Array.from(layer1),
    layer2: Array.from(layer2),
    references: Array.from(references),
  };
}
