// SPDX-License-Identifier: Apache-2.0

import { useEffect, useMemo, useState } from "react";
import { AnnotatorCanvas } from "./canvas/AnnotatorCanvas";
import type { Box } from "./metrics/geometry";
import { iou } from "./metrics/geometry";
import { computeWarehouseAlphas } from "./metrics/warehouseAlphas";
import { scoreSequence } from "./metrics/mot";
import { CiReportPanel } from "./report/CiReportPanel";
import { applyAnnotator, loadWarehouse, type Scene } from "./scenes/warehouse";

type Tab = "You" | "A" | "B" | "C" | "GT";

const HONESTY = [
  "Synthetic data only",
  "Simulation only",
  "Recorded CI scores sit beside a live annotator; this page does not train a model and does not use real robot images.",
];

const TRACK_MIN = 1;
const TRACK_MAX = 9999;
const COORD_MIN = -1000;
const COORD_MAX = 2000;
const SIZE_MAX = 2000;

function formatMetric(v: number | null | undefined): string {
  if (v === null || v === undefined) return "n/a";
  return v.toFixed(6);
}

function sanitizeYouFrame(boxes: Box[]): Box[] {
  const seen = new Set<number>();
  const out: Box[] = [];
  for (const b of boxes) {
    if (b.w <= 0 || b.h <= 0 || b.w > SIZE_MAX || b.h > SIZE_MAX) continue;
    if (b.x < COORD_MIN || b.x > COORD_MAX || b.y < COORD_MIN || b.y > COORD_MAX) continue;
    if (b.track_id < TRACK_MIN || b.track_id > TRACK_MAX || seen.has(b.track_id)) continue;
    seen.add(b.track_id);
    out.push(b);
  }
  return out.slice(0, 8);
}

function clampBox(b: Box): Box | null {
  const patch = { ...b };
  if (patch.w <= 0 || patch.h <= 0) return null;
  patch.w = Math.min(patch.w, SIZE_MAX);
  patch.h = Math.min(patch.h, SIZE_MAX);
  patch.x = Math.min(Math.max(patch.x, COORD_MIN), COORD_MAX);
  patch.y = Math.min(Math.max(patch.y, COORD_MIN), COORD_MAX);
  if (patch.track_id < TRACK_MIN || patch.track_id > TRACK_MAX) return null;
  return patch;
}

export default function App() {
  const [scene, setScene] = useState<Scene | null>(null);
  const [tab, setTab] = useState<Tab>("You");
  const [frame, setFrame] = useState(0);
  const [youFrames, setYouFrames] = useState<Box[][]>([]);
  const [selected, setSelected] = useState<number | null>(null);

  const reportOverrideUrl = useMemo(() => {
    const u = new URLSearchParams(window.location.search).get("reportUrl");
    return u ?? undefined;
  }, []);

  useEffect(() => {
    void loadWarehouse().then((s) => {
      setScene(s);
      setYouFrames(s.frames.map(() => []));
    });
  }, []);

  const traces = useMemo(() => {
    if (!scene) return null;
    return {
      GT: scene,
      A: applyAnnotator(scene, "A"),
      B: applyAnnotator(scene, "B"),
      C: applyAnnotator(scene, "C"),
    };
  }, [scene]);

  const warehouseAlphas = useMemo(() => (scene ? computeWarehouseAlphas(scene) : null), [scene]);

  if (!scene || !traces) return <div>Loading scene…</div>;

  const editable = tab === "You";
  const currentBoxes: Box[] = editable
    ? youFrames[frame]
    : tab === "GT"
      ? traces.GT.frames[frame].boxes
      : traces[tab].frames[frame].boxes;

  const setBoxes = (boxes: Box[]) => {
    if (!editable) return;
    setYouFrames((prev) => prev.map((fr, i) => (i === frame ? sanitizeYouFrame(boxes) : fr)));
  };

  const gtFrames = scene.frames.map((f) => f.boxes);
  const predFrames =
    tab === "You"
      ? youFrames
      : tab === "GT"
        ? gtFrames
        : traces[tab].frames.map((f) => f.boxes);

  const live = scoreSequence(gtFrames, tab === "You" ? youFrames : predFrames);
  const liveScore = live === "invalid" ? null : live;

  const frameGt = scene.frames[frame].boxes;
  const robotGt = frameGt.find((b) => b.class === "robot");
  let frameIou: number | null = null;
  if (robotGt && tab === "You") {
    const yours = youFrames[frame].find((b) => b.class === "robot");
    if (yours) frameIou = iou(robotGt, yours);
  }

  const editSelected = (patch: Partial<Box>) => {
    if (!editable || selected === null) return;
    const cur = { ...currentBoxes[selected], ...patch };
    const next = clampBox(cur);
    if (!next) {
      setBoxes(currentBoxes.filter((_, i) => i !== selected));
      setSelected(null);
      return;
    }
    const others = currentBoxes.filter((_, i) => i !== selected);
    if (others.some((b) => b.track_id === next.track_id)) return;
    setBoxes(others.concat([next]));
  };

  const pairwiseAbRaw = scoreSequence(
    traces.A.frames.map((f) => f.boxes),
    traces.B.frames.map((f) => f.boxes),
  );
  const pairwiseAb = pairwiseAbRaw === "invalid" ? null : pairwiseAbRaw;

  const gtBoxCount = traces.GT.frames[frame].boxes.length;

  return (
    <div style={{ fontFamily: "system-ui", padding: 16, maxWidth: 960 }}>
      {HONESTY.map((line) => (
        <p key={line} data-testid="honesty-line">
          {line}
        </p>
      ))}
      <div role="tablist" aria-label="Annotator tabs">
        {(["You", "A", "B", "C", "GT"] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={tab === t}
            data-testid={`tab-${t}`}
            onClick={() => {
              setTab(t);
              setSelected(null);
            }}
          >
            {t}
          </button>
        ))}
      </div>
      <div>
        <button type="button" data-testid="frame-prev" onClick={() => setFrame((f) => Math.max(0, f - 1))}>
          Previous frame
        </button>
        <label>
          Frame{" "}
          <input
            type="range"
            min={0}
            max={19}
            value={frame}
            data-testid="frame-slider"
            onChange={(e) => setFrame(Number(e.target.value))}
          />
          <span data-testid="frame-index">{frame}</span>
        </label>
        <button type="button" data-testid="frame-next" onClick={() => setFrame((f) => Math.min(19, f + 1))}>
          Next frame
        </button>
      </div>
      <AnnotatorCanvas
        width={640}
        height={360}
        boxes={currentBoxes}
        editable={editable}
        onChange={setBoxes}
        selectedIdx={selected}
        onSelect={setSelected}
        lockedSnapshotCount={tab === "GT" ? gtBoxCount : undefined}
      />
      {editable && selected !== null && currentBoxes[selected] && (
        <form data-testid="box-form" onSubmit={(e) => e.preventDefault()}>
          {(["x", "y", "w", "h"] as const).map((k) => (
            <label key={k}>
              {k}{" "}
              <input
                type="number"
                value={currentBoxes[selected][k]}
                onChange={(e) => editSelected({ [k]: Number(e.target.value) })}
              />
            </label>
          ))}
          <label>
            class{" "}
            <select
              value={currentBoxes[selected].class}
              onChange={(e) => editSelected({ class: e.target.value })}
            >
              <option value="robot">robot</option>
              <option value="pallet">pallet</option>
              <option value="cone">cone</option>
            </select>
          </label>
          <label>
            track_id{" "}
            <input
              type="number"
              value={currentBoxes[selected].track_id}
              onChange={(e) => editSelected({ track_id: Number(e.target.value) })}
            />
          </label>
          <button
            type="button"
            data-testid="delete-box"
            onClick={() => {
              setBoxes(currentBoxes.filter((_, i) => i !== selected));
              setSelected(null);
            }}
          >
            Delete
          </button>
        </form>
      )}
      <section data-testid="live-scores">
        <h2>Live scores vs GT ({tab})</h2>
        <p data-testid="alpha-shift-caveat">
          Label-level alpha does not capture annotator A&apos;s spatial shift; mean IoU does.
        </p>
        <p data-testid="warehouse-alpha-gtabc" data-score-raw={warehouseAlphas?.GTABC ?? "n/a"}>
          Warehouse label-level alpha (GT vs A, B, C): {formatMetric(warehouseAlphas?.GTABC ?? null)}
        </p>
        <p data-testid="live-robot-iou" data-score-raw={frameIou ?? "n/a"}>
          Frame robot IoU: {frameIou === null ? "n/a" : frameIou.toFixed(9)}
        </p>
        <p data-testid="score-mota" data-score="mota" data-score-raw={liveScore?.mota ?? "n/a"}>
          MOTA: {formatMetric(liveScore?.mota ?? null)}
        </p>
        <p data-testid="score-precision" data-score="precision" data-score-raw={liveScore?.precision ?? "n/a"}>
          Precision: {formatMetric(liveScore?.precision ?? null)}
        </p>
        <p data-testid="score-kappa" data-score="label_kappa" data-score-raw={liveScore?.label_kappa ?? "n/a"}>
          Label kappa: {formatMetric(liveScore?.label_kappa ?? null)}
        </p>
        <p
          data-testid="score-motp_mean_iou"
          data-score="motp_mean_iou"
          data-score-raw={liveScore?.motp_mean_iou ?? "n/a"}
        >
          MOTP mean IoU: {formatMetric(liveScore?.motp_mean_iou ?? null)}
        </p>
        <p data-testid="score-idf1" data-score="idf1" data-score-raw={liveScore?.idf1 ?? "n/a"}>
          IDF1: {formatMetric(liveScore?.idf1 ?? null)}
        </p>
      </section>
      <section data-testid="pairwise-scores">
        <h2>Pairwise (A vs B)</h2>
        <p data-testid="pairwise-ab-mota" data-score-raw={pairwiseAb?.mota ?? "n/a"}>
          MOTA: {formatMetric(pairwiseAb?.mota ?? null)}
        </p>
      </section>
      <CiReportPanel overrideUrl={reportOverrideUrl} />
    </div>
  );
}
