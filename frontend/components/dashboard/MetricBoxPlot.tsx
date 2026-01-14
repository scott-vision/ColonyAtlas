"use client";

import dynamic from "next/dynamic";
import type { Colony } from "../../lib/types";
import { METRIC_LABELS } from "../../lib/metrics";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

const DEFAULT_METRICS = [
  "area",
  "perimeter",
  "circularity",
  "solidity",
  "eccentricity",
  "aspect_ratio",
  "roughness"
] as const;

export default function MetricBoxPlot({
  colonies,
  metrics = DEFAULT_METRICS,
  labelOverrides
}: {
  colonies: Colony[];
  metrics?: string[];
  labelOverrides?: Record<string, string>;
}) {
  const traces = metrics.map((metric) => ({
    type: "box",
    name: labelOverrides?.[metric] ?? METRIC_LABELS[metric as keyof typeof METRIC_LABELS] ?? metric,
    y: colonies.map((colony) => colony.metrics[metric] || 0),
    boxpoints: false
  }));

  return (
    <div className="h-64">
      <Plot
        data={traces}
        layout={{
          paper_bgcolor: "#0f172a",
          plot_bgcolor: "#0f172a",
          font: { color: "#cbd5f5", size: 10 },
          margin: { l: 35, r: 10, t: 10, b: 60 },
          xaxis: { tickangle: 20 },
          showlegend: false
        }}
        config={{ displayModeBar: false }}
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
}
