"use client";

export default function ViewerToolbar({
  showMasks,
  showIds,
  colourBy,
  onToggleMasks,
  onToggleIds,
  onChangeColourBy
}: {
  showMasks: boolean;
  showIds: boolean;
  colourBy: "id" | "qc" | "cluster" | "condition";
  onToggleMasks: () => void;
  onToggleIds: () => void;
  onChangeColourBy: (value: "id" | "qc" | "cluster" | "condition") => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-300">
      <button
        type="button"
        onClick={onToggleMasks}
        className={`rounded-full px-3 py-1 ${
          showMasks ? "bg-cyan-500/20 text-cyan-200" : "bg-slate-800"
        }`}
      >
        {showMasks ? "Masks On" : "Masks Off"}
      </button>
      <button
        type="button"
        onClick={onToggleIds}
        className={`rounded-full px-3 py-1 ${
          showIds ? "bg-cyan-500/20 text-cyan-200" : "bg-slate-800"
        }`}
      >
        {showIds ? "IDs On" : "IDs Off"}
      </button>
      <div className="flex items-center gap-2">
        <span>Colour by</span>
        <select
          value={colourBy}
          onChange={(event) => onChangeColourBy(event.target.value as any)}
          className="rounded-lg border border-slate-700 bg-slate-950 px-2 py-1"
        >
          <option value="id">ID</option>
          <option value="qc">QC Flag</option>
          <option value="cluster">Cluster</option>
          <option value="condition">Condition</option>
        </select>
      </div>
    </div>
  );
}
