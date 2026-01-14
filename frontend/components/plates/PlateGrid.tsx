import type { Plate } from "../../lib/types";
import PlateCard from "./PlateCard";

export default function PlateGrid({
  plates,
  onAnalyze,
  analyzingId
}: {
  plates: Plate[];
  onAnalyze: (plateId: string) => void;
  analyzingId: string | null;
}) {
  if (plates.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-800 p-6 text-sm text-slate-500">
        No plates found. Upload images to get started.
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {plates.map((plate) => (
        <PlateCard
          key={plate.id}
          plate={plate}
          onAnalyze={onAnalyze}
          isAnalyzing={analyzingId === plate.id}
        />
      ))}
    </div>
  );
}
