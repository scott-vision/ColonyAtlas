import type { ReactNode } from "react";
import clsx from "clsx";

export default function Panel({
  title,
  action,
  children,
  className
}: {
  title: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={clsx(
        "rounded-2xl border border-slate-700 bg-slate-900",
        className
      )}
    >
      <header className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-200">{title}</h2>
        {action ? <div className="text-xs text-slate-400">{action}</div> : null}
      </header>
      <div className="p-4">{children}</div>
    </section>
  );
}
