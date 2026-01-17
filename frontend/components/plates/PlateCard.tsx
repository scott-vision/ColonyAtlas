"use client";

import Link from "next/link";
import type { Plate } from "../../lib/types";
import { getExportUrl, resolveApiUrl } from "../../lib/api";

export default function PlateCard({
  plate,
  onAnalyze,
  isAnalyzing,
  onDelete,
  isDeleting
}: {
  plate: Plate;
  onAnalyze: (plateId: string) => void;
  isAnalyzing: boolean;
  onDelete: (plateId: string) => void;
  isDeleting: boolean;
}) {
  const imageUrl = resolveApiUrl(plate.overlay_url || plate.image_url);
  const canAnalyze = plate.colony_count === 0;
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
      <button
        type="button"
        onClick={() => onDelete(plate.id)}
        disabled={isDeleting}
        aria-label={`Delete ${plate.name}`}
        className="absolute right-3 top-3 z-10 rounded-full border border-slate-700 bg-slate-900/80 p-2 text-slate-300 opacity-80 transition hover:border-red-400 hover:text-red-300 hover:opacity-100 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          className="h-4 w-4"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M9 3h6l1 2h4" />
          <path d="M6 7h12l-1 12a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7z" />
          <path d="M10 11v6M14 11v6" />
        </svg>
      </button>
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
