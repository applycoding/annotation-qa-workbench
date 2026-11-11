// SPDX-License-Identifier: Apache-2.0

import type { Box } from "../metrics/geometry";

export type Scene = {
  name: string;
  width: number;
  height: number;
  frames: { index: number; boxes: Box[] }[];
};

export async function loadWarehouse(): Promise<Scene> {
  const base = import.meta.env.BASE_URL;
  const res = await fetch(`${base}warehouse_v1.json`);
  return (await res.json()) as Scene;
}

export function applyAnnotator(scene: Scene, name: "A" | "B" | "C"): Scene {
  const out: Scene = JSON.parse(JSON.stringify(scene));
  if (name === "A") {
    for (const fr of out.frames) {
      for (const b of fr.boxes) {
        b.x += 2;
        b.y += 1;
      }
    }
  } else if (name === "B") {
    for (const fr of out.frames) {
      fr.boxes = fr.boxes
        .filter((b) => b.class !== "cone")
        .map((b) => ({
          ...b,
          class: fr.index >= 10 && b.class === "pallet" ? "robot" : b.class,
        }));
    }
  } else if (name === "C") {
    for (const fr of out.frames) {
      if (fr.index >= 10) {
        for (const b of fr.boxes) {
          if (b.track_id === 1) b.track_id = 2;
          else if (b.track_id === 2) b.track_id = 1;
        }
      }
    }
  }
  return out;
}
