import type { Colony } from "../../lib/types";
import { METRIC_KEYS, METRIC_LABELS } from "../../lib/metrics";

export default function MetricsTable({ colony }: { colony: Colony | null }) {
  if (!colony) {
    return <div className="text-sm text-slate-500">No colony selected.</div>;
  }

  return (
    <div className="space-y-3 text-xs text-slate-200">
      <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Colony ID</span>
          <span className="font-mono">{colony.id}</span>
        </div>
      </div>
      <div className="grid gap-2">
        {METRIC_KEYS.map((key) => {
          const value = colony.metrics[key];
          return (
            <div
              key={key}
              className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950 px-3 py-2"
            >
              <span className="text-slate-400">{METRIC_LABELS[key]}</span>
              <span className="font-mono">{value !== undefined ? value.toFixed(3) : "-"}</span>
            </div>
          );
        })}
        <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950 px-3 py-2">
          <span className="text-slate-400">QC Flags</span>
          <span>{colony.qc_flags.length ? colony.qc_flags.join(", ") : "None"}</span>
        </div>
      </div>
    </div>
  );
}
