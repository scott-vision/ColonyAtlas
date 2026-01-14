"use client";

import { useState } from "react";
import type { Plate } from "../../lib/types";
import { getExportUrl, getReportUrl, resolveApiUrl } from "../../lib/api";

export default function ExportMenu({ plate }: { plate: Plate }) {
  const [format, setFormat] = useState<"pdf" | "md">("pdf");
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-slate-200">Export</span>
        <span className="text-xs text-slate-500">Plate {plate.name}</span>
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-xs">
        <a
          href={getExportUrl(plate.id)}
          className="rounded-full bg-cyan-500/90 px-3 py-1 text-slate-900"
        >
          Export Colonies CSV
        </a>
        <a
          href={getReportUrl(plate.id, format)}
          className="rounded-full bg-slate-800 px-3 py-1 text-slate-200"
        >
          Download Report ({format.toUpperCase()})
        </a>
        {plate.overlay_url ? (
          <a
            href={resolveApiUrl(plate.overlay_url)}
            className="rounded-full bg-slate-800 px-3 py-1 text-slate-200"
          >
            Download Overlay
          </a>
        ) : null}
      </div>
      <div className="mt-3 flex items-center gap-4 text-xs text-slate-300">
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="report-format"
            value="pdf"
            checked={format === "pdf"}
            onChange={() => setFormat("pdf")}
          />
          PDF
        </label>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="report-format"
            value="md"
            checked={format === "md"}
            onChange={() => setFormat("md")}
          />
          Markdown
        </label>
      </div>
    </div>
  );
}
