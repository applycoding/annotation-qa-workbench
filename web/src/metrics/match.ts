// SPDX-License-Identifier: Apache-2.0

import { type Box, iou } from "./geometry";

const FORBIDDEN = 1e9;

function padCost(cost: number[][]): number[][] {
  const nRows = cost.length;
  const nCols = cost[0]?.length ?? 0;
  const size = Math.max(nRows, nCols);
  if (size === 0) return [];
  const padded: number[][] = Array.from({ length: size }, () => Array(size).fill(0));
  for (let i = 0; i < nRows; i++) {
    for (let j = 0; j < nCols; j++) padded[i][j] = cost[i][j];
  }
  return padded;
}

function permutations<T>(arr: T[], k: number): T[][] {
  if (k === 0) return [[]];
  if (arr.length < k) return [];
  const out: T[][] = [];
  for (let i = 0; i < arr.length; i++) {
    const rest = [...arr.slice(0, i), ...arr.slice(i + 1)];
    for (const tail of permutations(rest, k - 1)) out.push([arr[i], ...tail]);
  }
  return out;
}

export function exhaustiveMinCost(costMatrix: number[][]): Array<[number, number, number]> {
  const nRows = costMatrix.length;
  const nCols = costMatrix[0]?.length ?? 0;
  if (!nRows || !nCols) return [];
  const size = Math.max(nRows, nCols);
  let best = Number.POSITIVE_INFINITY;
  let bestPairs: Array<[number, number]> = [];
  const cols = Array.from({ length: nCols }, (_, j) => j);
  const extra = Array.from({ length: size - nCols }, (_, j) => nCols + j);
  for (const perm of permutations([...cols, ...extra], size)) {
    const pairs: Array<[number, number]> = [];
    let total = 0;
    for (let r = 0; r < nRows; r++) {
      const c = perm[r];
      if (c >= nCols) {
        pairs.push([r, -1]);
        continue;
      }
      total += costMatrix[r][c];
      pairs.push([r, c]);
    }
    const real = pairs.filter(([, c]) => c >= 0).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const key = real.map((p) => `${p[0]},${p[1]}`).join("|");
    const prevKey = bestPairs.map((p) => `${p[0]},${p[1]}`).join("|");
    if (total < best || (total === best && key < prevKey)) {
      best = total;
      bestPairs = real;
    }
  }
  return bestPairs.map(([r, c]) => [r, c, costMatrix[r][c]]);
}

function hungarianSquare(cost: number[][]): number[] {
  const n = cost.length;
  const u = new Array<number>(n + 1).fill(0);
  const v = new Array<number>(n + 1).fill(0);
  const p = new Array<number>(n + 1).fill(0);
  const way = new Array<number>(n + 1).fill(0);
  for (let i = 1; i <= n; i += 1) {
    p[0] = i;
    let j0 = 0;
    const minv = new Array<number>(n + 1).fill(Number.POSITIVE_INFINITY);
    const used = new Array<boolean>(n + 1).fill(false);
    do {
      used[j0] = true;
      const i0 = p[j0];
      let delta = Number.POSITIVE_INFINITY;
      let j1 = 0;
      for (let j = 1; j <= n; j += 1) {
        if (used[j]) continue;
        const cur = cost[i0 - 1][j - 1] - u[i0] - v[j];
        if (cur < minv[j]) {
          minv[j] = cur;
          way[j] = j0;
        }
        if (minv[j] < delta) {
          delta = minv[j];
          j1 = j;
        }
      }
      for (let j = 0; j <= n; j += 1) {
        if (used[j]) {
          u[p[j]] += delta;
          v[j] -= delta;
        } else {
          minv[j] -= delta;
        }
      }
      j0 = j1;
    } while (p[j0] !== 0);
    do {
      const j1w = way[j0];
      p[j0] = p[j1w];
      j0 = j1w;
    } while (j0);
  }
  const assign = new Array<number>(n).fill(-1);
  for (let j = 1; j <= n; j += 1) {
    if (p[j] > 0) assign[p[j] - 1] = j - 1;
  }
  return assign;
}

export function minCostAssignment(costMatrix: number[][]): Array<[number, number, number]> {
  if (!costMatrix.length) return [];
  const nRows = costMatrix.length;
  const nCols = costMatrix[0].length;
  if (Math.max(nRows, nCols) <= 8) {
    return exhaustiveMinCost(costMatrix);
  }
  const padded = padCost(costMatrix);
  const assign = hungarianSquare(padded);
  const result: Array<[number, number, number]> = [];
  for (let row = 0; row < nRows; row += 1) {
    const col = assign[row];
    if (col >= 0 && col < nCols) {
      result.push([row, col, padded[row][col]]);
    }
  }
  result.sort((a, b) => (a[0] !== b[0] ? a[0] - b[0] : a[1] - b[1]));
  return result;
}

export function matchBoxes(
  gt: Box[],
  pred: Box[],
  thresh = 0.5,
  iouFn: (a: Box, b: Box) => number = iou,
): Array<[number, number, number]> {
  if (gt.length > 8 || pred.length > 8) throw new Error("invalid");
  if (!gt.length || !pred.length) return [];
  const cost = gt.map((g) =>
    pred.map((p) => {
      const ov = iouFn(g, p);
      return ov >= thresh ? 1 - ov : FORBIDDEN;
    }),
  );
  return minCostAssignment(cost)
    .filter(([, , c]) => c < FORBIDDEN)
    .map(([i, j]) => [i, j, iouFn(gt[i], pred[j])] as [number, number, number]);
}
