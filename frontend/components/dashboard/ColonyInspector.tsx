"use client";

import type { Colony } from "../../lib/types";
import MaskPreview from "./MaskPreview";
import MetricsTable from "./MetricsTable";

export default function ColonyInspector({
  colony,
  imageUrl
}: {
  colony: Colony | null;
  imageUrl: string;
}) {
  const handleCopy = async () => {
    if (!colony) return;
    const payload = {
      id: colony.id,
      metrics: colony.metrics,
      qc_flags: colony.qc_flags
    };
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>Colony Details</span>
        <button
          type="button"
          onClick={handleCopy}
          className="rounded-full bg-slate-800 px-3 py-1 text-slate-200"
        >
          Copy metrics
        </button>
      </div>
      <MaskPreview colony={colony} imageUrl={imageUrl} />
      <MetricsTable colony={colony} />
    </div>
  );
}
