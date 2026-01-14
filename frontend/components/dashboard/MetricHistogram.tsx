"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";
import type { Colony, MetricKey } from "../../lib/types";
import { METRIC_LABELS } from "../../lib/metrics";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

function buildHistogram(values: number[], binCount = 20) {
  if (values.length === 0) return { bins: [], counts: [] };
  const min = Math.min(...values);
  const max = Math.max(...values);
  const step = (max - min) / binCount || 1;
  const bins = Array.from({ length: binCount }, (_, i) => min + i * step);
  const counts = Array(binCount).fill(0);
  values.forEach((value) => {
    const index = Math.min(binCount - 1, Math.floor((value - min) / step));
    counts[index] += 1;
  });
  return { bins, counts };
}

export default function MetricHistogram({
  colonies,
  metric,
  selectedColonyId,
  onMetricChange
}: {
  colonies: Colony[];
  metric: MetricKey;
  selectedColonyId: string | null;
  onMetricChange: (metric: MetricKey) => void;
}) {
  const values = useMemo(
    () => colonies.map((colony) => colony.metrics[metric] || 0),
    [colonies, metric]
  );
  const { bins, counts } = useMemo(() => buildHistogram(values), [values]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>Distribution</span>
        <select
          value={metric}
          onChange={(event) => onMetricChange(event.target.value as MetricKey)}
          className="rounded-lg border border-slate-700 bg-slate-950 px-2 py-1"
        >
          {Object.entries(METRIC_LABELS).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </div>
      <div className="h-48">
        <Plot
          data={[
            {
              type: "bar",
              x: bins,
              y: counts,
              marker: { color: "#22d3ee" },
              hovertemplate: "Value %{x:.2f}<br>Count %{y}<extra></extra>"
            }
          ]}
          layout={{
            paper_bgcolor: "#0f172a",
            plot_bgcolor: "#0f172a",
            font: { color: "#cbd5f5", size: 10 },
            margin: { l: 30, r: 10, t: 10, b: 30 },
            xaxis: { title: METRIC_LABELS[metric] },
            yaxis: { title: "Count" },
            showlegend: false
          }}
          config={{ displayModeBar: false }}
          style={{ width: "100%", height: "100%" }}
        />
      </div>
      <p className="text-xs text-slate-500">
        Selected colony: {selectedColonyId ? selectedColonyId.slice(0, 6) : "None"}
      </p>
    </div>
  );
}
