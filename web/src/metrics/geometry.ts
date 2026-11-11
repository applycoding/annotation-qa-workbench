// SPDX-License-Identifier: Apache-2.0

export type Box = { x: number; y: number; w: number; h: number; class: string; track_id: number };

export function boxArea(w: number, h: number): number {
  return w > 0 && h > 0 ? w * h : 0;
}

export function iou(a: Box, b: Box): number {
  const vals = [a.x, a.y, a.w, a.h, b.x, b.y, b.w, b.h];
  if (vals.some((v) => !Number.isFinite(v))) return 0;
  if (a.w <= 0 || a.h <= 0 || b.w <= 0 || b.h <= 0) return 0;
  const interW = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x));
  const interH = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
  const inter = interW * interH;
  const union = boxArea(a.w, a.h) + boxArea(b.w, b.h) - inter;
  return union <= 0 ? 0 : inter / union;
}
