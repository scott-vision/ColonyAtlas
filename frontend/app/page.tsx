export default function Home() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center gap-8 text-center">
      <img src="/Logo.png" alt="ColonyAtlas logo" className="h-28 w-28 rounded-2xl" />
      <div className="max-w-2xl space-y-4">
        <h1 className="text-3xl font-semibold text-slate-100 md:text-4xl">
          ColonyAtlas
        </h1>
        <p className="text-sm text-slate-400 md:text-base">
          Interactive morphology analysis for bacterial colonies. Upload plates, run
          segmentation, and explore colony-level metrics with synchronized visuals.
        </p>
      </div>
      <a
        href="/upload"
        className="rounded-full bg-cyan-500/90 px-6 py-3 text-sm font-semibold text-slate-900 transition hover:bg-cyan-400"
      >
        Get Started
      </a>
    </div>
  );
}
