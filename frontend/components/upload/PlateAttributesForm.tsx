"use client";

import type { PlateAttributes } from "../../lib/types";

export type PlateAttributesDraft = {
  plate_diameter_mm: string;
  species: string;
  hours_post_inoculation: string;
  volume: string;
  treatment_description: string;
  notes: string;
};

export default function PlateAttributesForm({
  value,
  onChange
}: {
  value: PlateAttributesDraft;
  onChange: (next: PlateAttributesDraft) => void;
}) {
  return (
    <div className="grid gap-3">
      <label className="text-xs text-slate-400">Plate Diameter (mm)</label>
      <input
        type="number"
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        value={value.plate_diameter_mm}
        onChange={(event) =>
          onChange({ ...value, plate_diameter_mm: event.target.value })
        }
      />
      <label className="text-xs text-slate-400">Species</label>
      <input
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        value={value.species}
        onChange={(event) => onChange({ ...value, species: event.target.value })}
        placeholder="e.g. E. coli"
      />
      <label className="text-xs text-slate-400">Hours Post Inoculation</label>
      <input
        type="number"
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        value={value.hours_post_inoculation}
        onChange={(event) =>
          onChange({ ...value, hours_post_inoculation: event.target.value })
        }
      />
      <label className="text-xs text-slate-400">Volume (normalization factor)</label>
      <input
        type="number"
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        value={value.volume}
        onChange={(event) => onChange({ ...value, volume: event.target.value })}
      />
      <label className="text-xs text-slate-400">Treatment Description</label>
      <input
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        value={value.treatment_description}
        onChange={(event) =>
          onChange({ ...value, treatment_description: event.target.value })
        }
        placeholder="e.g. Antibiotic X"
      />
      <label className="text-xs text-slate-400">Notes</label>
      <textarea
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        value={value.notes}
        onChange={(event) => onChange({ ...value, notes: event.target.value })}
        rows={3}
      />
    </div>
  );
}
