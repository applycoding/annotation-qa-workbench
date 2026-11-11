// SPDX-License-Identifier: Apache-2.0

import { applyAnnotator, type Scene } from "../scenes/warehouse";
import type { Box } from "./geometry";
import { matchBoxes } from "./match";
import { krippendorffAlphaNominal } from "./alpha";

function gtClass(gtFrames: Box[][], frameIdx: number, trackId: number): string | null {
  for (const g of gtFrames[frameIdx]) {
    if (g.track_id === trackId) return g.class;
  }
  return null;
}

function classAfterMatch(
  gtFrames: Box[][],
  predFrames: Box[][],
  frameIdx: number,
  trackId: number,
): string | null {
  const gtBoxes = gtFrames[frameIdx];
  const predBoxes = predFrames[frameIdx];
  for (const [gi, pj] of matchBoxes(gtBoxes, predBoxes)) {
    if (gtBoxes[gi].track_id === trackId) return predBoxes[pj].class;
  }
  return null;
}

function alphaMatrix(
  gtFrames: Box[][],
  raterFrames: Box[][][],
  includeGt = false,
): (string | null)[][] {
  const units: (string | null)[][] = [];
  const trackIds = [1, 2, 3];
  for (let frameIdx = 0; frameIdx < gtFrames.length; frameIdx += 1) {
    for (const tid of trackIds) {
      const row: (string | null)[] = [];
      if (includeGt) row.push(gtClass(gtFrames, frameIdx, tid));
      for (const predFrames of raterFrames) {
        row.push(classAfterMatch(gtFrames, predFrames, frameIdx, tid));
      }
      units.push(row);
    }
  }
  return units;
}

export type WarehouseAlphaKey = "AC" | "AB" | "BC" | "ABC" | "GTABC";

export function computeWarehouseAlphas(scene: Scene): Record<WarehouseAlphaKey, number | null> {
  const gtFrames = scene.frames.map((f) => f.boxes);
  const aFrames = applyAnnotator(scene, "A").frames.map((f) => f.boxes);
  const bFrames = applyAnnotator(scene, "B").frames.map((f) => f.boxes);
  const cFrames = applyAnnotator(scene, "C").frames.map((f) => f.boxes);
  return {
    AC: krippendorffAlphaNominal(alphaMatrix(gtFrames, [aFrames, cFrames])),
    AB: krippendorffAlphaNominal(alphaMatrix(gtFrames, [aFrames, bFrames])),
    BC: krippendorffAlphaNominal(alphaMatrix(gtFrames, [bFrames, cFrames])),
    ABC: krippendorffAlphaNominal(alphaMatrix(gtFrames, [aFrames, bFrames, cFrames])),
    GTABC: krippendorffAlphaNominal(
      alphaMatrix(gtFrames, [aFrames, bFrames, cFrames], true),
    ),
  };
}
