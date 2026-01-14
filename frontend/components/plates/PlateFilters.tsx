"use client";

export default function PlateFilters({
  search,
  onSearch
}: {
  search: string;
  onSearch: (value: string) => void;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-900 p-4 md:flex-row md:items-center">
      <input
        value={search}
        onChange={(event) => onSearch(event.target.value)}
        placeholder="Search plates or metadata"
        className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
      />
      <select className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm">
        <option>QC status: Any</option>
        <option>QC flagged</option>
        <option>QC clean</option>
      </select>
      <select className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm">
        <option>Sort: Newest</option>
        <option>Colony count</option>
      </select>
    </div>
  );
}
