// SPDX-License-Identifier: Apache-2.0

export function krippendorffAlphaNominal(matrix: Array<Array<string | null>>): number | null {
  if (!matrix.length) return null;
  let nValues = 0;
  let sumOcc = 0;
  const nCTotal = new Map<string, number>();
  for (const unit of matrix) {
    const present = unit.filter((v): v is string => v !== null);
    const m = present.length;
    if (m < 2) continue;
    nValues += m;
    const counts = new Map<string, number>();
    for (const v of present) counts.set(v, (counts.get(v) ?? 0) + 1);
    for (const [c, nc] of counts) {
      nCTotal.set(c, (nCTotal.get(c) ?? 0) + nc);
      sumOcc += (nc * (nc - 1)) / (m - 1);
    }
  }
  if (nValues < 2) return null;
  let denomStat = 0;
  for (const nc of nCTotal.values()) denomStat += nc * (nc - 1);
  const num = (nValues - 1) * sumOcc - denomStat;
  const den = nValues * (nValues - 1) - denomStat;
  if (den === 0) return null;
  return num / den;
}
