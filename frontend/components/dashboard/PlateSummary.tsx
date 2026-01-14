"use client";

import type { Plate } from "../../lib/types";

export default function PlateSummary({ plate }: { plate: Plate }) {
  const derived = plate.derived_stats || {};
  const colorHex =
    typeof derived.average_color_hex === "string" ? derived.average_color_hex : "#000000";

  return (
    <div className="space-y-3 text-xs text-slate-200">
      <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
        <p className="text-slate-400">Plate Attributes</p>
        <div className="mt-2 space-y-1">
          <div>Diameter: {plate.attributes?.plate_diameter_mm ?? 90} mm</div>
          <div>Species: {plate.attributes?.species || "N/A"}</div>
          <div>Hours post inoculation: {plate.attributes?.hours_post_inoculation ?? 0}</div>
          <div>Volume: {plate.attributes?.volume ?? 1}</div>
          <div>Treatment: {plate.attributes?.treatment_description || "N/A"}</div>
          <div>Notes: {plate.attributes?.notes || "N/A"}</div>
        </div>
      </div>
      <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
        <p className="text-slate-400">Derived Summary</p>
        <div className="mt-2 space-y-1">
          <div>Colony count: {derived.colony_count ?? plate.colony_count}</div>
          <div>Volume adjusted count: {derived.volume_adjusted_count ?? "-"}</div>
          <div>Colony density (per mm^2): {derived.colony_density_per_mm2 ?? "-"}</div>
          <div className="flex items-center gap-2">
            <span>Average color:</span>
            <span className="font-mono">{derived.average_color_hex ?? "N/A"}</span>
            <span
              className="h-3 w-3 rounded-full border border-slate-600"
              style={{ backgroundColor: colorHex }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
