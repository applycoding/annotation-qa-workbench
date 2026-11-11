// SPDX-License-Identifier: Apache-2.0

export function cohenKappa(a: string[], b: string[]): number | null {
  const n = a.length;
  if (n !== b.length || n === 0) return null;
  let agree = 0;
  const ca = new Map<string, number>();
  const cb = new Map<string, number>();
  for (let i = 0; i < n; i++) {
    if (a[i] === b[i]) agree++;
    ca.set(a[i], (ca.get(a[i]) ?? 0) + 1);
    cb.set(b[i], (cb.get(b[i]) ?? 0) + 1);
  }
  const po = agree / n;
  const cats = new Set([...ca.keys(), ...cb.keys()]);
  let pe = 0;
  for (const c of cats) pe += ((ca.get(c) ?? 0) / n) * ((cb.get(c) ?? 0) / n);
  if (pe === 1) return null;
  return (po - pe) / (1 - pe);
}
