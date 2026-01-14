"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";
import type { Colony, MetricKey } from "../../lib/types";
import { METRIC_LABELS } from "../../lib/metrics";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

function pointColor(colony: Colony, colourBy: string, selected: boolean) {
  if (selected) return "#e2e8f0";
  if (colourBy === "qc") {
    return colony.qc_flags.length ? "#f59e0b" : "#22d3ee";
  }
  return "#22d3ee";
}

export default function MetricScatter({
  colonies,
  xMetric,
  yMetric,
  selectedColonyId,
  colourBy,
  onChangeXMetric,
  onChangeYMetric,
  onSelectColony
}: {
  colonies: Colony[];
  xMetric: MetricKey;
  yMetric: MetricKey;
  selectedColonyId: string | null;
  colourBy: "id" | "qc" | "cluster" | "condition";
  onChangeXMetric: (metric: MetricKey) => void;
  onChangeYMetric: (metric: MetricKey) => void;
  onSelectColony: (colonyId: string) => void;
}) {
  const plotData = useMemo(() => {
    const x = colonies.map((colony) => colony.metrics[xMetric] || 0);
    const y = colonies.map((colony) => colony.metrics[yMetric] || 0);
    const customdata = colonies.map((colony) => colony.id);
    const colors = colonies.map((colony) =>
      pointColor(colony, colourBy, colony.id === selectedColonyId)
    );
    return { x, y, customdata, colors };
  }, [colonies, xMetric, yMetric, colourBy, selectedColonyId]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
        <span>Scatter</span>
        <select
          value={xMetric}
          onChange={(event) => onChangeXMetric(event.target.value as MetricKey)}
          className="rounded-lg border border-slate-700 bg-slate-950 px-2 py-1"
        >
          {Object.entries(METRIC_LABELS).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
        <select
          value={yMetric}
          onChange={(event) => onChangeYMetric(event.target.value as MetricKey)}
          className="rounded-lg border border-slate-700 bg-slate-950 px-2 py-1"
        >
          {Object.entries(METRIC_LABELS).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </div>
      <div className="h-96">
        <Plot
          data={[
            {
              type: "scattergl",
              mode: "markers",
              x: plotData.x,
              y: plotData.y,
              customdata: plotData.customdata,
              marker: {
                color: plotData.colors,
                size: 7,
                opacity: 0.85
              },
              hovertemplate: "Colony %{customdata}<br>%{xaxis.title.text}: %{x:.2f}<br>%{yaxis.title.text}: %{y:.2f}<extra></extra>"
            }
          ]}
          layout={{
            paper_bgcolor: "#0f172a",
            plot_bgcolor: "#0f172a",
            font: { color: "#cbd5f5", size: 10 },
            margin: { l: 55, r: 10, t: 10, b: 45 },
            xaxis: { title: METRIC_LABELS[xMetric], automargin: true },
            yaxis: { title: METRIC_LABELS[yMetric], automargin: true },
            showlegend: false
          }}
          config={{ displayModeBar: false }}
          style={{ width: "100%", height: "100%" }}
          onClick={(event) => {
            const point = event?.points?.[0];
            if (point?.customdata) {
              onSelectColony(point.customdata as string);
            }
          }}
        />
      </div>
    </div>
  );
}
