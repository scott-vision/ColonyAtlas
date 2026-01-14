"use client";

export default function UploadQueue({
  files,
  onRemove
}: {
  files: File[];
  onRemove: (index: number) => void;
}) {
  if (files.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-700 p-4 text-sm text-slate-500">
        No files added yet.
      </div>
    );
  }

  return (
    <ul className="space-y-2">
      {files.map((file, index) => (
        <li
          key={`${file.name}-${index}`}
          className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950 px-3 py-2"
        >
          <div>
            <p className="text-sm text-slate-200">{file.name}</p>
            <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
          <button
            type="button"
            className="text-xs text-amber-300 hover:text-amber-200"
            onClick={() => onRemove(index)}
          >
            Remove
          </button>
        </li>
      ))}
    </ul>
  );
}
