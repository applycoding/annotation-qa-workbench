// SPDX-License-Identifier: Apache-2.0

import { useEffect, useRef, useState } from "react";
import type { Box } from "../metrics/geometry";

const CLASS_COLOR: Record<string, string> = {
  robot: "#2F6FED",
  pallet: "#C47A12",
  cone: "#C22A2A",
};

type Props = {
  width: number;
  height: number;
  boxes: Box[];
  editable: boolean;
  onChange: (boxes: Box[]) => void;
  selectedIdx: number | null;
  onSelect: (idx: number | null) => void;
  lockedSnapshotCount?: number;
};

export function AnnotatorCanvas({
  width,
  height,
  boxes,
  editable,
  onChange,
  selectedIdx,
  onSelect,
  lockedSnapshotCount,
}: Props) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [drag, setDrag] = useState<{ x0: number; y0: number; x1: number; y1: number } | null>(null);

  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const ctx = c.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = "#1B1F24";
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = "#2A313A";
    for (let x = 0; x < width; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
    boxes.forEach((b, idx) => {
      ctx.fillStyle = CLASS_COLOR[b.class] ?? "#888";
      ctx.globalAlpha = idx === selectedIdx ? 0.85 : 0.65;
      ctx.fillRect(b.x, b.y, b.w, b.h);
      ctx.globalAlpha = 1;
      ctx.strokeStyle = idx === selectedIdx ? "#fff" : "#222";
      ctx.strokeRect(b.x, b.y, b.w, b.h);
    });
    if (drag && editable) {
      const x = Math.min(drag.x0, drag.x1);
      const y = Math.min(drag.y0, drag.y1);
      const w = Math.abs(drag.x1 - drag.x0);
      const h = Math.abs(drag.y1 - drag.y0);
      ctx.strokeStyle = "#9cf";
      ctx.strokeRect(x, y, w, h);
    }
  }, [boxes, drag, height, selectedIdx, width, editable]);

  const toLocal = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const sx = width / rect.width;
    const sy = height / rect.height;
    return {
      x: (e.clientX - rect.left) * sx,
      y: (e.clientY - rect.top) * sy,
    };
  };

  const trySelect = (x: number, y: number) => {
    for (let i = boxes.length - 1; i >= 0; i--) {
      const b = boxes[i];
      if (x >= b.x && x < b.x + b.w && y >= b.y && y < b.y + b.h) {
        onSelect(i);
        return;
      }
    }
    onSelect(null);
  };

  const countAttr = lockedSnapshotCount ?? boxes.length;
  return (
    <div data-testid="canvas-box-count" data-count={String(countAttr)}>
    <canvas
      ref={ref}
      width={width}
      height={height}
      style={{
        width: "640px",
        height: "360px",
        cursor: editable ? "crosshair" : "default",
      }}
      data-testid="annotator-canvas"
      onMouseDown={(e) => {
        if (!editable) return;
        const p = toLocal(e);
        trySelect(p.x, p.y);
        setDrag({ x0: p.x, y0: p.y, x1: p.x, y1: p.y });
      }}
      onMouseMove={(e) => {
        if (!drag || !editable) return;
        const p = toLocal(e);
        setDrag({ ...drag, x1: p.x, y1: p.y });
      }}
      onMouseUp={(e) => {
        if (!editable || !drag) return;
        const p = toLocal(e);
        const x = Math.min(drag.x0, p.x);
        const y = Math.min(drag.y0, p.y);
        const w = Math.abs(p.x - drag.x0);
        const h = Math.abs(p.y - drag.y0);
        setDrag(null);
        if (w < 2 || h < 2) return;
        if (boxes.length >= 8) return;
        const nb: Box = { x, y, w, h, class: "robot", track_id: 1 };
        onChange([...boxes, nb]);
        onSelect(boxes.length);
      }}
    />
    </div>
  );
}
