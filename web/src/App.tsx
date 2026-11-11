// SPDX-License-Identifier: Apache-2.0

import { useEffect, useMemo, useState } from "react";
import { AnnotatorCanvas } from "./canvas/AnnotatorCanvas";
import type { Box } from "./metrics/geometry";
import { iou } from "./metrics/geometry";
import { scoreSequence } from "./metrics/mot";
import { CiReportPanel } from "./report/CiReportPanel";
import { applyAnnotator, loadWarehouse, type Scene } from "./scenes/warehouse";

type Tab = "You" | "A" | "B" | "C" | "GT";

const HONESTY = [
  "Synthetic data only",
  "Simulation only",
  "Recorded CI scores sit beside a live annotator; this page does not train a model and does not use real robot images.",
];

function formatMetric(v: number | null | undefined): string {
  if (v === null || v === undefined) return "n/a";
  return v.toFixed(6);
}

export default function App({ reportOverrideUrl }: { reportOverrideUrl?: string }) {
  const [scene, setScene] = useState<Scene | null>(null);
  const [tab, setTab] = useState<Tab>("You");
  const [frame, setFrame] = useState(0);
  const [youFrames, setYouFrames] = useState<Box[][]>([]);
  const [selected, setSelected] = useState<number | null>(null);

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

  if (!scene || !traces) return <div>Loading scene…</div>;

  const editable = tab === "You";
  const currentBoxes: Box[] = editable
    ? youFrames[frame]
    : tab === "GT"
      ? traces.GT.frames[frame].boxes
      : traces[tab].frames[frame].boxes;

  const setBoxes = (boxes: Box[]) => {
    if (!editable) return;
    setYouFrames((prev) => prev.map((fr, i) => (i === frame ? boxes : fr)));
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
    setBoxes(
      currentBoxes.map((b, i) => (i === selected ? { ...b, ...patch } : b)),
    );
  };

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
      <AnnotatorCanvas
        width={640}
        height={360}
        boxes={currentBoxes}
        editable={editable}
        onChange={setBoxes}
        selectedIdx={selected}
        onSelect={setSelected}
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
          <button type="button" data-testid="delete-box" onClick={() => setBoxes(currentBoxes.filter((_, i) => i !== selected))}>
            Delete
          </button>
        </form>
      )}
      <section data-testid="live-scores">
        <h2>Live scores vs GT ({tab})</h2>
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
      <CiReportPanel overrideUrl={reportOverrideUrl} />
    </div>
  );
}
