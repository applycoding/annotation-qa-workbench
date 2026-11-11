// SPDX-License-Identifier: Apache-2.0

import { type Box, iou } from "./geometry";
import { matchBoxes, minCostAssignment } from "./match";
import { cohenKappa } from "./kappa";

export type MotScore = {
  fn: number;
  fp: number;
  idsw: number;
  gt_count: number;
  pred_count: number;
  matches: number;
  mota: number | null;
  motp_mean_iou: number | null;
  idtp: number;
  idfn: number;
  idfp: number;
  idf1: number | null;
  precision: number | null;
  recall: number | null;
  f1: number | null;
  label_kappa: number | null;
  n_matched: number;
};

function countPairs(
  gtFrames: Box[][],
  predFrames: Box[][],
  thresh: number,
  matchOnly: boolean,
): Map<string, number> {
  const counts = new Map<string, number>();
  const bump = (g: number, p: number) => {
    const k = `${g},${p}`;
    counts.set(k, (counts.get(k) ?? 0) + 1);
  };
  for (let f = 0; f < gtFrames.length; f++) {
    const gt = gtFrames[f];
    const pred = predFrames[f];
    if (gt.length > 8 || pred.length > 8) throw new Error("invalid");
    if (matchOnly) {
      for (const [gi, pj] of matchBoxes(gt, pred, thresh).map((t) => [t[0], t[1]] as const)) {
        bump(gt[gi].track_id, pred[pj].track_id);
      }
    } else {
      for (let gi = 0; gi < gt.length; gi++) {
        for (let pj = 0; pj < pred.length; pj++) {
          if (iou(gt[gi], pred[pj]) >= thresh) bump(gt[gi].track_id, pred[pj].track_id);
        }
      }
    }
  }
  return counts;
}

export function scoreSequence(gtFrames: Box[][], predFrames: Box[][]): MotScore | "invalid" {
  const gtCount = gtFrames.reduce((s, f) => s + f.length, 0);
  const predCount = predFrames.reduce((s, f) => s + f.length, 0);
  for (const fr of gtFrames) if (fr.length > 8) return "invalid";
  for (const fr of predFrames) if (fr.length > 8) return "invalid";

  if (gtCount === 0 && predCount === 0) {
    return {
      fn: 0,
      fp: 0,
      idsw: 0,
      gt_count: 0,
      pred_count: 0,
      matches: 0,
      mota: 1,
      motp_mean_iou: null,
      idtp: 0,
      idfn: 0,
      idfp: 0,
      idf1: 1,
      precision: null,
      recall: null,
      f1: null,
      label_kappa: null,
      n_matched: 0,
    };
  }

  let fn = 0;
  let fp = 0;
  let matches = 0;
  let idsw = 0;
  let iouSum = 0;
  const la: string[] = [];
  const lb: string[] = [];
  const last = new Map<number, number>();

  for (let f = 0; f < gtFrames.length; f++) {
    const pairs = matchBoxes(gtFrames[f], predFrames[f]);
    const mgt = new Set(pairs.map((p) => p[0]));
    const mpr = new Set(pairs.map((p) => p[1]));
    fn += gtFrames[f].length - mgt.size;
    fp += predFrames[f].length - mpr.size;
    matches += pairs.length;
    for (const [gi, pj, ov] of pairs) {
      iouSum += ov;
      la.push(gtFrames[f][gi].class);
      lb.push(predFrames[f][pj].class);
      const gid = gtFrames[f][gi].track_id;
      const pid = predFrames[f][pj].track_id;
      if (last.has(gid) && last.get(gid) !== pid) idsw++;
      last.set(gid, pid);
    }
  }

  let counts: Map<string, number>;
  try {
    counts = countPairs(gtFrames, predFrames, 0.5, false);
  } catch {
    return "invalid";
  }
  const gtIds = [...new Set(gtFrames.flat().map((b) => b.track_id))].sort((a, b) => a - b);
  const prIds = [...new Set(predFrames.flat().map((b) => b.track_id))].sort((a, b) => a - b);
  if (gtIds.length > 32 || prIds.length > 32) return "invalid";
  const cost = gtIds.map((g) => prIds.map((p) => -(counts.get(`${g},${p}`) ?? 0)));
  const assigned = minCostAssignment(cost);
  let idtp = 0;
  for (const [i, j] of assigned) idtp += counts.get(`${gtIds[i]},${prIds[j]}`) ?? 0;
  const idfn = gtCount - idtp;
  const idfp = predCount - idtp;
  const denom = 2 * idtp + idfp + idfn;
  const idf1 = denom ? (2 * idtp) / denom : null;
  const motp = matches ? iouSum / matches : null;
  const mota = 1 - (fn + fp + idsw) / gtCount;

  let precision: number | null = predCount ? matches / predCount : null;
  let recall: number | null = gtCount ? matches / gtCount : null;
  let f1: number | null =
    precision !== null && recall !== null && precision + recall
      ? (2 * precision * recall) / (precision + recall)
      : null;
  if (predCount === 0 && gtCount > 0) {
    precision = null;
    recall = 0;
    f1 = null;
    return {
      fn,
      fp,
      idsw,
      gt_count: gtCount,
      pred_count: predCount,
      matches,
      mota: 0,
      motp_mean_iou: null,
      idtp,
      idfn,
      idfp,
      idf1: 0,
      precision,
      recall,
      f1,
      label_kappa: null,
      n_matched: matches,
    };
  }

  return {
    fn,
    fp,
    idsw,
    gt_count: gtCount,
    pred_count: predCount,
    matches,
    mota,
    motp_mean_iou: motp,
    idtp,
    idfn,
    idfp,
    idf1,
    precision,
    recall,
    f1,
    label_kappa: cohenKappa(la, lb),
    n_matched: matches,
  };
}
