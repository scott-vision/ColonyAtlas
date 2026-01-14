"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Panel from "../../components/layout/Panel";
import UploadDropzone from "../../components/upload/UploadDropzone";
import PlateAttributesForm, {
  type PlateAttributesDraft
} from "../../components/upload/PlateAttributesForm";
import UploadQueue from "../../components/upload/UploadQueue";
import { analyzePlates, updatePlateAttributes, uploadImages } from "../../lib/api";
import type { Plate, PlateAttributes } from "../../lib/types";

const defaultAttributes: PlateAttributesDraft = {
  plate_diameter_mm: "90",
  species: "",
  hours_post_inoculation: "0",
  volume: "1",
  treatment_description: "",
  notes: ""
};

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [status, setStatus] = useState<"idle" | "uploading" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [uploadedPlates, setUploadedPlates] = useState<Plate[]>([]);
  const [attributesByPlate, setAttributesByPlate] = useState<
    Record<string, PlateAttributesDraft>
  >({});
  const [savingId, setSavingId] = useState<string | null>(null);
  const router = useRouter();

  const handleFilesSelected = (incoming: File[]) => {
    setFiles((prev) => [...prev, ...incoming]);
  };

  const handleRemove = (index: number) => {
    setFiles((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleStart = async () => {
    if (files.length === 0) return;
    setStatus("uploading");
    setError(null);
    try {
      const upload = await uploadImages(files);
      setUploadedPlates(upload.plates);
      const nextAttributes: Record<string, PlateAttributesDraft> = {};
      upload.plates.forEach((plate) => {
        if (plate.attributes) {
          nextAttributes[plate.id] = {
            plate_diameter_mm: String(plate.attributes.plate_diameter_mm ?? 90),
            species: plate.attributes.species ?? "",
            hours_post_inoculation: String(plate.attributes.hours_post_inoculation ?? 0),
            volume: String(plate.attributes.volume ?? 1),
            treatment_description: plate.attributes.treatment_description ?? "",
            notes: plate.attributes.notes ?? ""
          };
        } else {
          nextAttributes[plate.id] = { ...defaultAttributes };
        }
      });
      setAttributesByPlate(nextAttributes);
      setStatus("idle");
      setFiles([]);
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Upload failed");
    }
  };

  const handleAttributeChange = (plateId: string, next: PlateAttributesDraft) => {
    setAttributesByPlate((prev) => ({ ...prev, [plateId]: next }));
  };

  const handleSave = async (plateId: string) => {
    const attrs = attributesByPlate[plateId];
    if (!attrs) return;
    const parsed: PlateAttributes = {
      plate_diameter_mm: Number(attrs.plate_diameter_mm || 0),
      species: attrs.species,
      hours_post_inoculation: Number(attrs.hours_post_inoculation || 0),
      volume: Number(attrs.volume || 1),
      treatment_description: attrs.treatment_description,
      notes: attrs.notes
    };
    setSavingId(plateId);
    setError(null);
    try {
      const updated = await updatePlateAttributes(plateId, parsed);
      setUploadedPlates((prev) =>
        prev.map((plate) => (plate.id === updated.id ? updated : plate))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save details");
    } finally {
      setSavingId(null);
    }
  };

  const handleAnalyzeAll = async () => {
    if (uploadedPlates.length === 0) return;
    setError(null);
    try {
      await analyzePlates({ plate_ids: uploadedPlates.map((plate) => plate.id) });
      router.push("/plates");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Panel title="Upload Plate Images">
        <div className="space-y-4">
          <UploadDropzone onFilesSelected={handleFilesSelected} />
        </div>
      </Panel>

      <Panel
        title="Upload Queue"
        action={
          <span className="rounded-full bg-slate-800 px-2 py-1">{files.length} files</span>
        }
      >
        <div className="space-y-4">
          <UploadQueue files={files} onRemove={handleRemove} />
          {error ? <p className="text-sm text-red-400">{error}</p> : null}
          <button
            type="button"
            className="w-full rounded-xl bg-cyan-500/90 px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-40"
            onClick={handleStart}
            disabled={files.length === 0 || status === "uploading"}
          >
            {status === "uploading" ? "Uploading..." : "Upload Images"}
          </button>
        </div>
      </Panel>

      {uploadedPlates.length > 0 ? (
        <Panel title="Plate Details">
          <div className="space-y-6">
            {uploadedPlates.map((plate) => (
              <div
                key={plate.id}
                className="rounded-xl border border-slate-800 bg-slate-950 p-4"
              >
                <div className="mb-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-100">{plate.name}</p>
                    <p className="text-xs text-slate-500">{plate.id}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleSave(plate.id)}
                    disabled={savingId === plate.id}
                    className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-200 disabled:opacity-50"
                  >
                    {savingId === plate.id ? "Saving..." : "Save Details"}
                  </button>
                </div>
                <PlateAttributesForm
                  value={attributesByPlate[plate.id] || { ...defaultAttributes }}
                  onChange={(next) => handleAttributeChange(plate.id, next)}
                />
              </div>
            ))}
            {error ? <p className="text-sm text-red-400">{error}</p> : null}
            <button
              type="button"
              onClick={handleAnalyzeAll}
              className="w-full rounded-xl bg-cyan-500/90 px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-cyan-400"
            >
              Segment Plates
            </button>
          </div>
        </Panel>
      ) : null}
    </div>
  );
}
