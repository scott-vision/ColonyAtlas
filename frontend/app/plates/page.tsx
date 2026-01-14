"use client";

import { useEffect, useMemo, useState } from "react";
import PlateFilters from "../../components/plates/PlateFilters";
import PlateGrid from "../../components/plates/PlateGrid";
import { analyzePlates, getPlates } from "../../lib/api";
import type { Plate } from "../../lib/types";

export default function PlatesPage() {
  const [plates, setPlates] = useState<Plate[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);

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
      ) : (
        <PlateGrid plates={filtered} onAnalyze={handleAnalyze} analyzingId={analyzingId} />
      )}
    </div>
  );
}
