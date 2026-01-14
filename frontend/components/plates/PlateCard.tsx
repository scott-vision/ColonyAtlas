"use client";

import Link from "next/link";
import type { Plate } from "../../lib/types";
import { getExportUrl, resolveApiUrl } from "../../lib/api";

export default function PlateCard({
  plate,
  onAnalyze,
  isAnalyzing
}: {
  plate: Plate;
  onAnalyze: (plateId: string) => void;
  isAnalyzing: boolean;
}) {
  const imageUrl = resolveApiUrl(plate.overlay_url || plate.image_url);
  const canAnalyze = plate.colony_count === 0;
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
      <div className="aspect-[4/3] overflow-hidden bg-slate-950">
        <img
          src={imageUrl}
          alt={plate.name}
          className="h-full w-full object-cover"
        />
      </div>
      <div className="space-y-3 p-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">{plate.name}</h3>
          <p className="text-xs text-slate-500">{new Date(plate.created_at).toLocaleString()}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-slate-800 px-2 py-1 text-xs text-slate-300">
            Colonies: {plate.colony_count}
          </span>
          <span className="rounded-full bg-slate-800 px-2 py-1 text-xs text-slate-300">
            QC Flags: {Object.values(plate.qc_summary || {}).reduce((a, b) => a + b, 0)}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href={`/dashboard/${plate.id}`}
            className="rounded-full bg-cyan-500/90 px-3 py-1 text-xs font-semibold text-slate-900"
          >
            Open Dashboard
          </Link>
          {canAnalyze ? (
            <button
              type="button"
              onClick={() => onAnalyze(plate.id)}
              disabled={isAnalyzing}
              className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-200 disabled:opacity-50"
            >
              {isAnalyzing ? "Segmenting..." : "Segment"}
            </button>
          ) : null}
          <a href={getExportUrl(plate.id)} className="text-xs text-slate-300 hover:text-white">
            Export CSV
          </a>
        </div>
      </div>
    </div>
  );
}
