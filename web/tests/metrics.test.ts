// SPDX-License-Identifier: Apache-2.0

import { describe, expect, it } from "vitest";
import { applyAnnotator, type Scene } from "../src/scenes/warehouse";
import type { Box } from "../src/metrics/geometry";
import { iou } from "../src/metrics/geometry";
import { cohenKappa } from "../src/metrics/kappa";
import { scoreSequence } from "../src/metrics/mot";
import { loadExpected, rationalFloat } from "./expectedUtil";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const TOL = 1e-12;
const scene = JSON.parse(
  readFileSync(resolve(__dirname, "../../fixtures/scenes/warehouse_v1.json"), "utf8"),
) as Scene;

function box(xywh: number[]): Box {
  return { x: xywh[0], y: xywh[1], w: xywh[2], h: xywh[3], class: "robot", track_id: 1 };
}

describe("IoU parity", () => {
  const cases = loadExpected<{ cases: Array<{ id: string; a: number[]; b: number[]; rational: [number, number] }> }>(
    "iou_cases.json",
  ).cases;
  for (const c of cases) {
    it(c.id, () => {
      expect(Math.abs(iou(box(c.a), box(c.b)) - rationalFloat(c))).toBeLessThanOrEqual(TOL);
    });
  }
});

describe("warehouse gates", () => {
  const gates = loadExpected<Record<string, Record<string, unknown>>>("warehouse_gates.json");
  for (const name of ["A", "B", "C", "gt"] as const) {
    const key = name === "gt" ? "gt" : name;
    it(`annotator ${name}`, () => {
      const gt = scene.frames.map((f) => f.boxes);
      const pred =
        name === "gt" ? gt : applyAnnotator(scene, name).frames.map((f) => f.boxes);
      const s = scoreSequence(gt, pred);
      expect(s).not.toBe("invalid");
      if (s === "invalid") return;
      const exp = gates[key] as Record<string, { rational: [number, number] }>;
      for (const field of ["mota", "idf1", "label_kappa", "motp_mean_iou"] as const) {
        if (exp[field]) {
          const actual = s[field];
          expect(actual).not.toBeNull();
          expect(Math.abs((actual ?? 0) - rationalFloat(exp[field]))).toBeLessThanOrEqual(TOL);
        }
      }
    });
  }
});

describe("kappa parity", () => {
  const kappa = loadExpected<Record<string, { rational: [number, number] }>>("kappa_cases.json");
  it("half", () => {
    const got = cohenKappa(["A", "A", "A", "B"], ["A", "A", "B", "B"]);
    expect(got).not.toBeNull();
    expect(Math.abs((got ?? 0) - rationalFloat(kappa.half))).toBeLessThanOrEqual(TOL);
  });
});

describe("mot toys", () => {
  const toys = loadExpected<Record<string, Record<string, unknown>>>("mot_toys.json");

  it("gt zero pred positive", () => {
    const s = scoreSequence([], [[{ x: 0, y: 0, w: 10, h: 10, class: "robot", track_id: 1 }]]);
    expect(s).not.toBe("invalid");
    if (s === "invalid") return;
    expect(s.mota).toBeNull();
    expect(s.recall).toBeNull();
    expect(s.idf1).toBeNull();
  });

  it("empty both", () => {
    const exp = toys.empty_both as { mota: { rational: [number, number] }; idf1: { rational: [number, number] } };
    const s = scoreSequence([[]], [[]]);
    expect(s).not.toBe("invalid");
    if (s === "invalid") return;
    expect(Math.abs((s.mota ?? 0) - rationalFloat(exp.mota))).toBeLessThanOrEqual(TOL);
    expect(Math.abs((s.idf1 ?? 0) - rationalFloat(exp.idf1))).toBeLessThanOrEqual(TOL);
  });
});
