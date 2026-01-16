import Link from "next/link";

const navItems = [
  { href: "/upload", label: "Upload" },
  { href: "/plates", label: "Plate Overview" },
  { href: "/plates", label: "Analysis Dashboard" }
];

export default function TopNav() {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-3">
          <img src="/Logo.png" alt="ColonyAtlas logo" className="h-8 w-8 rounded-lg" />
          <span className="text-lg font-semibold">ColonyAtlas</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-full px-3 py-1 text-slate-300 transition hover:bg-slate-800 hover:text-white"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="text-xs text-slate-400">Status: Idle</div>
      </div>
    </header>
  );
}
