// SPDX-License-Identifier: Apache-2.0

import { describe, expect, it } from "vitest";
import { exhaustiveMinCost, minCostAssignment } from "../src/metrics/match";

const FORBIDDEN = 1e9;

describe("assignment", () => {
  it("exhaustive n6 matches hungarian", () => {
    const ious = Array.from({ length: 6 }, (_, i) =>
      Array.from({ length: 6 }, (_, j) => (i === j ? 1 : 0)),
    );
    const cost = ious.map((row) => row.map((v) => (v < 0.5 ? FORBIDDEN : 1 - v)));
    const h = new Set(minCostAssignment(cost).map(([i, j]) => `${i},${j}`));
    const e = new Set(exhaustiveMinCost(cost).map(([i, j]) => `${i},${j}`));
    expect(h).toEqual(e);
  });

  it("hungarian handles 10x10 identity", () => {
    const cost = Array.from({ length: 10 }, (_, i) =>
      Array.from({ length: 10 }, (_, j) => (i === j ? 0 : FORBIDDEN)),
    );
    const got = minCostAssignment(cost);
    expect(got.length).toBe(10);
    for (const [i, j] of got) expect(i).toBe(j);
  });
});
