"use client";

export interface UploadMetadata {
  experiment: string;
  condition: string;
  replicate: string;
  pixelSize: string;
}

export default function UploadMetadataForm({
  value,
  onChange
}: {
  value: UploadMetadata;
  onChange: (next: UploadMetadata) => void;
}) {
  return (
    <div className="grid gap-3">
      <label className="text-xs text-slate-400">Experiment</label>
      <input
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        value={value.experiment}
        onChange={(event) => onChange({ ...value, experiment: event.target.value })}
        placeholder="e.g. Antibiotic screen"
      />
      <label className="text-xs text-slate-400">Condition / Strain</label>
      <input
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        value={value.condition}
        onChange={(event) => onChange({ ...value, condition: event.target.value })}
        placeholder="WT + stress"
      />
      <label className="text-xs text-slate-400">Replicate</label>
      <input
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        value={value.replicate}
        onChange={(event) => onChange({ ...value, replicate: event.target.value })}
        placeholder="1"
      />
      <label className="text-xs text-slate-400">Pixel Size (um/px)</label>
      <input
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        value={value.pixelSize}
        onChange={(event) => onChange({ ...value, pixelSize: event.target.value })}
        placeholder="0.5"
      />
    </div>
  );
}
