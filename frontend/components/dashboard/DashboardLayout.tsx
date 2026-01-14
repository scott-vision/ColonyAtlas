import type { ReactNode } from "react";

export default function DashboardLayout({
  viewer,
  summary,
  inspector,
  histogram,
  boxplotShape,
  boxplotSize,
  scatter,
  exportMenu
}: {
  viewer: ReactNode;
  summary: ReactNode;
  inspector: ReactNode;
  histogram: ReactNode;
  boxplotShape: ReactNode;
  boxplotSize: ReactNode;
  scatter: ReactNode;
  exportMenu: ReactNode;
}) {
  return (
    <div className="grid gap-4 lg:grid-cols-12">
      <div className="lg:col-span-8 space-y-4">{viewer}</div>
      <div className="lg:col-span-4 space-y-4">
        {inspector}
      </div>
      <div className="lg:col-span-6">{summary}</div>
      <div className="lg:col-span-6">{histogram}</div>
      <div className="lg:col-span-6">{boxplotShape}</div>
      <div className="lg:col-span-6">{boxplotSize}</div>
      <div className="lg:col-span-12">{scatter}</div>
      <div className="lg:col-span-12 flex justify-end">{exportMenu}</div>
    </div>
  );
}
