"use client";

import { useEffect, useMemo, useState } from "react";
import PlateFilters from "../../components/plates/PlateFilters";
import PlateGrid from "../../components/plates/PlateGrid";
import { analyzePlates, deletePlate, getPlates } from "../../lib/api";
import type { Plate } from "../../lib/types";

export default function PlatesPage() {
  const [plates, setPlates] = useState<Plate[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    getPlates()
      .then((data) => {
        if (mounted) {
          setPlates(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load plates");
          setLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  const filtered = useMemo(() => {
    const lower = search.toLowerCase();
    return plates.filter((plate) => {
      if (plate.name.toLowerCase().includes(lower)) return true;
      if (plate.metadata) {
        return Object.values(plate.metadata).some((value) =>
          value.toLowerCase().includes(lower)
        );
      }
      return false;
    });
  }, [plates, search]);

  const handleAnalyze = async (plateId: string) => {
    setAnalyzingId(plateId);
    setError(null);
    try {
      await analyzePlates({ plate_ids: [plateId] });
      const refreshed = await getPlates();
      setPlates(refreshed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze plate");
    } finally {
      setAnalyzingId(null);
    }
  };

  const handleDelete = async (plateId: string) => {
    const plate = plates.find((item) => item.id === plateId);
    const name = plate?.name || "this plate";
    if (!window.confirm(`Delete ${name}? This cannot be undone.`)) {
      return;
    }
    setDeletingId(plateId);
    setError(null);
    try {
      await deletePlate(plateId);
      setPlates((current) => current.filter((item) => item.id !== plateId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete plate");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <PlateFilters search={search} onSearch={setSearch} />
      {loading ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-sm text-slate-400">
          Loading plates...
        </div>
      ) : error ? (
        <div className="rounded-2xl border border-red-800 bg-red-950/50 p-6 text-sm text-red-200">
          {error}
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-sm text-slate-300">
          <p className="mb-3">No results yet, upload an image to get started.</p>
          <a
            href="/upload"
            className="inline-flex rounded-full bg-cyan-500/90 px-4 py-2 text-xs font-semibold text-slate-900"
          >
            Go to Upload
          </a>
        </div>
      ) : (
        <div className="space-y-3">
          {analyzingId ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-300">
              <div className="mb-2">Segmenting plate...</div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                <div className="h-full w-1/2 animate-pulse rounded-full bg-cyan-400" />
              </div>
            </div>
          ) : null}
          <PlateGrid
            plates={filtered}
            onAnalyze={handleAnalyze}
            analyzingId={analyzingId}
            onDelete={handleDelete}
            deletingId={deletingId}
          />
        </div>
      )}
    </div>
  );
}
