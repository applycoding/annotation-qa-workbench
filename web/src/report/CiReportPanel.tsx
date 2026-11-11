// SPDX-License-Identifier: Apache-2.0

import { useEffect, useState } from "react";

type Report = Record<string, unknown>;

export type ReportState = { status: "loading" } | { status: "ok"; data: Report } | { status: "error"; message: string };

export function CiReportPanel({ overrideUrl }: { overrideUrl?: string }) {
  const [state, setState] = useState<ReportState>({ status: "loading" });

  useEffect(() => {
    const url = overrideUrl ?? `${import.meta.env.BASE_URL}report.json`;
    void fetch(url)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as Report;
        if (import.meta.env.PROD && data.sample === true) throw new Error("sample report in production");
        setState({ status: "ok", data });
      })
      .catch((err: Error) => setState({ status: "error", message: err.message }));
  }, [overrideUrl]);

  if (state.status === "loading") return <div data-testid="ci-report">Loading CI report…</div>;
  if (state.status === "error")
    return (
      <div data-testid="ci-report-error" role="alert">
        CI report unavailable: {state.message}
      </div>
    );
  const mota = (state.data.scores as Record<string, { mota: number }>).B.mota;
  return (
    <div data-testid="ci-report">
      <h3>Recorded CI report</h3>
      <p data-testid="ci-report-b-mota" data-score-raw={String(mota)}>
        Annotator B MOTA (CI): {Number(mota).toFixed(6)}
      </p>
    </div>
  );
}
