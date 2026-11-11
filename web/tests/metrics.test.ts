// SPDX-License-Identifier: Apache-2.0

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { applyAnnotator } from "../src/scenes/warehouse";
import type { Scene } from "../src/scenes/warehouse";
import { iou } from "../src/metrics/geometry";
import { matchBoxes, minCostAssignment } from "../src/metrics/match";
import { scoreSequence } from "../src/metrics/mot";

const TOL = 1e-12;
const scene = JSON.parse(
  readFileSync(resolve(__dirname, "../../fixtures/scenes/warehouse_v1.json"), "utf8"),
) as Scene;

describe("warehouse parity", () => {
  it("annotator A motp_mean_iou", () => {
    const gt = scene.frames.map((f) => f.boxes);
    const a = applyAnnotator(scene, "A").frames.map((f) => f.boxes);
    const s = scoreSequence(gt, a);
    expect(s).not.toBe("invalid");
    if (s === "invalid") return;
    const expected = 32619964 / 39538911;
    expect(Math.abs((s.motp_mean_iou ?? 0) - expected)).toBeLessThanOrEqual(TOL);
  });
});
