"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import DashboardLayout from "../../../components/dashboard/DashboardLayout";
import ImageViewer from "../../../components/dashboard/ImageViewer";
import ViewerToolbar from "../../../components/dashboard/ViewerToolbar";
import ColonyInspector from "../../../components/dashboard/ColonyInspector";
import MetricHistogram from "../../../components/dashboard/MetricHistogram";
import MetricBoxPlot from "../../../components/dashboard/MetricBoxPlot";
import MetricScatter from "../../../components/dashboard/MetricScatter";
import ExportMenu from "../../../components/dashboard/ExportMenu";
import PlateSummary from "../../../components/dashboard/PlateSummary";
import Panel from "../../../components/layout/Panel";
import { getPlate, getPlateColonies, resolveApiUrl } from "../../../lib/api";
import type { Colony, Plate } from "../../../lib/types";
import { DashboardProvider, useDashboardStore } from "../../../lib/store";

function DashboardContent({ plate, colonies }: { plate: Plate; colonies: Colony[] }) {
  const { state, dispatch } = useDashboardStore();
  const selectedColony = useMemo(
    () => colonies.find((colony) => colony.id === state.selectedColonyId) || null,
    [colonies, state.selectedColonyId]
  );
  const hasMmMetrics = useMemo(
    () =>
      colonies.some(
        (colony) =>
          typeof colony.metrics.area_mm2 === "number" &&
          colony.metrics.area_mm2 > 0 &&
          typeof colony.metrics.perimeter_mm === "number" &&
          colony.metrics.perimeter_mm > 0
      ),
    [colonies]
  );

  useEffect(() => {
    if (!state.selectedColonyId && colonies.length > 0) {
      dispatch({ type: "selectColony", colonyId: colonies[0].id });
    }
  }, [colonies, dispatch, state.selectedColonyId]);

  return (
    <DashboardLayout
      viewer={
        <Panel title="Image Viewer">
          <div className="space-y-3">
            <ViewerToolbar
              showMasks={state.showMasks}
              showOutlines={state.showOutlines}
              showIds={state.showIds}
              colourBy={state.colourBy}
              onToggleMasks={() => dispatch({ type: "toggleMasks" })}
              onToggleOutlines={() => dispatch({ type: "toggleOutlines" })}
              onToggleIds={() => dispatch({ type: "toggleIds" })}
              onChangeColourBy={(value) =>
                dispatch({ type: "setColourBy", colourBy: value })
              }
            />
            <ImageViewer
              baseImageUrl={resolveApiUrl(plate.image_url)}
              overlayImageUrl={plate.overlay_url ? resolveApiUrl(plate.overlay_url) : null}
              colonies={colonies}
              selectedColonyId={state.selectedColonyId}
              hoveredColonyId={state.hoveredColonyId}
              showMasks={state.showMasks}
              showOutlines={state.showOutlines}
              showIds={state.showIds}
              colourBy={state.colourBy}
              onHoverColony={(colonyId) => dispatch({ type: "hoverColony", colonyId })}
              onSelectColony={(colonyId) => dispatch({ type: "selectColony", colonyId })}
            />
          </div>
        </Panel>
      }
      summary={
        <Panel title="Plate Summary">
          <PlateSummary plate={plate} />
        </Panel>
      }
      inspector={
        <Panel title="Colony Inspector">
          <ColonyInspector colony={selectedColony} imageUrl={resolveApiUrl(plate.image_url)} />
        </Panel>
      }
      histogram={
        <Panel title="Metric Histogram">
          <MetricHistogram
            colonies={colonies}
            metric={state.xMetric}
            selectedColonyId={state.selectedColonyId}
            onMetricChange={(metric) => dispatch({ type: "setXMetric", metric })}
          />
        </Panel>
      }
      boxplotShape={
        <Panel title="Shape Metrics Box Plot">
          <MetricBoxPlot
            colonies={colonies}
            metrics={["circularity", "solidity", "eccentricity", "aspect_ratio", "roughness"]}
          />
        </Panel>
      }
      boxplotSize={
        <Panel title="Size Metrics Box Plot">
          <MetricBoxPlot
            colonies={colonies}
            metrics={hasMmMetrics ? ["area_mm2", "perimeter_mm"] : ["area", "perimeter"]}
            labelOverrides={{
              area_mm2: "Area (mm^2)",
              perimeter_mm: "Perimeter (mm)"
            }}
          />
        </Panel>
      }
      scatter={
        <Panel title="Metric Scatter">
          <MetricScatter
            colonies={colonies}
            xMetric={state.xMetric}
            yMetric={state.yMetric}
            selectedColonyId={state.selectedColonyId}
            colourBy={state.colourBy}
            onChangeXMetric={(metric) => dispatch({ type: "setXMetric", metric })}
            onChangeYMetric={(metric) => dispatch({ type: "setYMetric", metric })}
            onSelectColony={(colonyId) => dispatch({ type: "selectColony", colonyId })}
          />
        </Panel>
      }
      exportMenu={<ExportMenu plate={plate} />}
    />
  );
}

export default function DashboardPage() {
  const params = useParams();
  const plateId = Array.isArray(params?.plateId) ? params?.plateId[0] : params?.plateId;
  const [plate, setPlate] = useState<Plate | null>(null);
  const [colonies, setColonies] = useState<Colony[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!plateId) return;
    setLoading(true);
    Promise.all([getPlate(plateId), getPlateColonies(plateId)])
      .then(([plateData, colonyData]) => {
        setPlate(plateData);
        setColonies(colonyData);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load plate");
        setLoading(false);
      });
  }, [plateId]);

  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-sm text-slate-400">
        Loading dashboard...
      </div>
    );
  }

  if (error || !plate || !plateId) {
    return (
      <div className="rounded-2xl border border-red-800 bg-red-950/50 p-6 text-sm text-red-200">
        {error || "Plate not found."}
      </div>
    );
  }

  return (
    <DashboardProvider plateId={plateId}>
      <DashboardContent plate={plate} colonies={colonies} />
    </DashboardProvider>
  );
}
