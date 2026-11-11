// SPDX-License-Identifier: Apache-2.0

/** Nominal Krippendorff's alpha; rows are units, columns are raters. */

export function krippendorffAlphaNominal(
  reliabilityMatrix: (string | null)[][],
): number | null {
  if (!reliabilityMatrix.length) return null;
  const categoryTotals = new Map<string, number>();
  let sumOcc = 0;
  let nValues = 0;

  for (const unit of reliabilityMatrix) {
    const present = unit.filter((v): v is string => v !== null);
    const m = present.length;
    if (m < 2) continue;
    nValues += m;
    const counts = new Map<string, number>();
    for (const v of present) counts.set(v, (counts.get(v) ?? 0) + 1);
    for (const [c, nC] of counts) {
      categoryTotals.set(c, (categoryTotals.get(c) ?? 0) + nC);
      sumOcc += (nC * (nC - 1)) / (m - 1);
    }
  }

  if (nValues < 2) return null;
  let denomStat = 0;
  for (const nC of categoryTotals.values()) denomStat += nC * (nC - 1);
  const numerator = (nValues - 1) * sumOcc - denomStat;
  const denominator = nValues * (nValues - 1) - denomStat;
  if (denominator === 0) return null;
  return numerator / denominator;
}
