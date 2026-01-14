"use client";

import { useRef, useState } from "react";

export default function UploadDropzone({
  onFilesSelected
}: {
  onFilesSelected: (files: File[]) => void;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = (fileList: FileList | null) => {
    if (!fileList) return;
    onFilesSelected(Array.from(fileList));
  };

  return (
    <div
      className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition ${
        isDragging ? "border-cyan-400 bg-cyan-400/10" : "border-slate-700"
      }`}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setIsDragging(false);
        handleFiles(event.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        className="hidden"
        onChange={(event) => handleFiles(event.target.files)}
      />
      <p className="text-sm text-slate-300">Drag & drop plate images here</p>
      <p className="mt-1 text-xs text-slate-500">PNG, JPG, or TIFF</p>
      <div className="mt-4 flex gap-2">
        <button
          type="button"
          className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-200 hover:bg-slate-700"
          onClick={() => inputRef.current?.click()}
        >
          Select Files
        </button>
      </div>
    </div>
  );
}
