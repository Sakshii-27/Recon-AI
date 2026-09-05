"use client";

import { useState } from "react";
import { RefreshCw, Play } from "lucide-react";
import { runReconciliation } from "@/services/api";

export function RunReconciliation({
  onRunComplete,
}: {
  onRunComplete: (data: any) => void;
}) {
  const [records, setRecords] = useState(1000);
  const [seed, setSeed] = useState(42);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRun() {
    try {
      setLoading(true);
      setError(null);
      const data = await runReconciliation({ records, seed });
      onRunComplete(data);
    } catch (err: any) {
      setError(err.message || "Failed to run reconciliation");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-4">
      <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100">
        <label className="text-sm font-medium text-slate-600">Records:</label>
        <input
          type="number"
          value={records}
          onChange={(e) => setRecords(Number(e.target.value))}
          className="w-20 bg-transparent text-sm font-semibold text-slate-800 focus:outline-none"
          min={13}
          max={10000}
        />
      </div>
      
      <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100">
        <label className="text-sm font-medium text-slate-600">Seed:</label>
        <input
          type="number"
          value={seed}
          onChange={(e) => setSeed(Number(e.target.value))}
          className="w-16 bg-transparent text-sm font-semibold text-slate-800 focus:outline-none"
        />
      </div>

      <button
        onClick={handleRun}
        disabled={loading}
        className="group flex items-center justify-center space-x-2 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white px-6 py-2.5 rounded-xl text-sm font-semibold shadow-lg shadow-indigo-200 transition-all duration-300 hover:-translate-y-0.5 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none"
      >
        {loading ? (
          <RefreshCw className="w-4 h-4 animate-spin" />
        ) : (
          <Play className="w-4 h-4 transition-transform group-hover:scale-110" />
        )}
        <span>{loading ? "Running..." : "Run Reconciliation"}</span>
      </button>

      {error && <span className="text-sm font-medium text-red-600 bg-red-50 px-3 py-1 rounded-md">{error}</span>}
    </div>
  );
}
