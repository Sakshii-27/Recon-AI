import { ShieldCheck } from "lucide-react";

export function Header({
  hasRun,
  metadata,
}: {
  hasRun: boolean;
  metadata: any;
}) {
  const lastRunTime = hasRun && metadata ? new Date().toLocaleTimeString() : null;
  return (
    <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center pb-6 border-b border-slate-100">
      <div className="flex items-center space-x-4">
        <div className="bg-gradient-to-br from-indigo-500 to-violet-600 p-2.5 rounded-xl shadow-lg shadow-indigo-200">
          <ShieldCheck className="w-7 h-7 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-700 tracking-tight">ReconPulse AI</h1>
          <p className="text-sm font-medium text-slate-500">
            Finance Control Center
          </p>
        </div>
      </div>
      
      <div className="mt-4 sm:mt-0 flex flex-col items-end">
        {hasRun ? (
          <>
            <span className="text-sm font-semibold text-slate-700 bg-white/50 px-3 py-1 rounded-full border border-slate-200 shadow-sm backdrop-blur-sm">
              Status: <span className="text-emerald-600">Reconciled with Exceptions</span>
            </span>
            <span className="text-xs font-medium text-slate-400 mt-2">
              Last Run: {lastRunTime} (Seed: {metadata?.seed})
            </span>
          </>
        ) : (
          <span className="text-sm font-medium text-slate-500 bg-white/50 px-3 py-1 rounded-full border border-slate-200 shadow-sm backdrop-blur-sm">
            Status: Waiting for reconciliation run...
          </span>
        )}
      </div>
    </header>
  );
}
