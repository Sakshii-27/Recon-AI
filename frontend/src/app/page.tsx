"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/dashboard/Header";
import { KpiCards } from "@/components/dashboard/KpiCards";
import { ReconciliationHealth } from "@/components/dashboard/ReconciliationHealth";
import { FinancialSummary } from "@/components/dashboard/FinancialSummary";
import { ExceptionAnalytics } from "@/components/dashboard/ExceptionAnalytics";
import { RecentExceptions } from "@/components/dashboard/RecentExceptions";
import { BenchmarkPanel } from "@/components/dashboard/BenchmarkPanel";
import { RunReconciliation } from "@/components/dashboard/RunReconciliation";
import { CashPositionPanel } from "@/components/dashboard/CashPositionPanel";
import { CashForecastPanel } from "@/components/dashboard/CashForecastPanel";
import { FinanceCopilot } from "@/components/copilot/FinanceCopilot";
import {
  fetchBenchmark,
  fetchExceptions,
  fetchFinancialSummary,
  BenchmarkBaselineResponse,
  ExceptionListResponse,
  FinancialSummaryResponse,
  ReconciliationSummary,
  API_BASE_URL,
} from "@/services/api";
import { AlertCircle, ArrowRight } from "lucide-react";

export default function Dashboard() {
  const [hasRun, setHasRun] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [benchmark, setBenchmark] = useState<BenchmarkBaselineResponse | null>(null);
  const [exceptions, setExceptions] = useState<ExceptionListResponse | null>(null);
  const [finance, setFinance] = useState<FinancialSummaryResponse | null>(null);
  const [summary, setSummary] = useState<ReconciliationSummary | null>(null);
  const [metadata, setMetadata] = useState<any>(null);
  const [cashPosition, setCashPosition] = useState<any>(null);
  const [cashForecast, setCashForecast] = useState<any>(null);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch benchmark (always exists unless API is completely down)
      const benchData = await fetchBenchmark();
      setBenchmark(benchData);

      // 2. Fetch exceptions to determine if a run exists
      const excData = await fetchExceptions();
      
      // If we got exceptions successfully, it means a run exists in memory
      setExceptions(excData);
      
      // 3. Fetch finance
      const finData = await fetchFinancialSummary();
      setFinance(finData);
      
      // 4. Fetch Cash Position & Forecast
      const { fetchCashPosition, fetchCashForecast, fetchSummary } = await import("@/services/api");
      const [posData, foreData, summaryData] = await Promise.all([
        fetchCashPosition(),
        fetchCashForecast(),
        fetchSummary().catch(() => null)
      ]);
      setCashPosition(posData);
      setCashForecast(foreData);
      if (summaryData) setSummary(summaryData);
      
      setHasRun(true);
    } catch (err: any) {
      if (err.message?.includes("Failed to fetch exceptions") || err.message?.includes("Not Found")) {
        // This is expected if there is no run in memory
        setHasRun(false);
      } else {
        // Only show hard errors if it's not a missing run
        setError(err.message || "Failed to load dashboard data");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleRunComplete(data: any) {
    setLoading(true);
    try {
      // The `data` contains summary, finance_summary, metadata, and exceptions.
      // We can use it directly, but to be sure the latest data is also what the other
      // endpoints serve, we can just fetch exceptions again since `data` only has raw exception dicts,
      // and we want the structured `ExceptionListResponse`.
      const excData = await fetchExceptions();
      setExceptions(excData);
      
      setFinance(data.financial_summary);
      setSummary(data.summary);
      setMetadata(data.metadata);
      const { fetchCashPosition, fetchCashForecast } = await import("@/services/api");
      const [posData, foreData] = await Promise.all([
        fetchCashPosition(),
        fetchCashForecast()
      ]);
      setCashPosition(posData);
      setCashForecast(foreData);
      
    } catch (err: any) {
      setError("Failed to refresh data after run.");
    } finally {
      setLoading(false);
    }
  }

  // Use the actual summary if we have it, else fallback to a safe empty object if somehow not fetched
  const currentSummary = summary ? summary : (hasRun ? {
    total_records: 0, 
    matched: 0,
    exceptions: 0,
    match_rate: 0,
    value_reconciled: 0,
    safe_autonomous_rate: 0, 
  } : null);

  return (
    <div className="min-h-screen font-sans selection:bg-indigo-200 selection:text-indigo-900">
      <div className="max-w-7xl mx-auto p-4 sm:p-8 space-y-8">
        
        {/* Header & Run Controls */}
        <div className="bg-white/60 backdrop-blur-xl p-8 rounded-3xl border border-white/60 shadow-xl shadow-indigo-100/40 space-y-8 transition-all hover:bg-white/70">
          <Header hasRun={hasRun} metadata={metadata} />
          
          <div className="flex flex-col sm:flex-row items-center justify-between">
            <p className="text-sm text-slate-500 max-w-xl">
              Configure parameters to start a deterministic reconciliation batch.
              Ground truth is isolated and used only for the benchmark.
            </p>
            <div className="mt-4 sm:mt-0">
              <RunReconciliation onRunComplete={handleRunComplete} />
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-50 text-red-800 rounded-lg flex items-center shadow-sm">
            <AlertCircle className="w-5 h-5 mr-3 flex-shrink-0" />
            <span className="font-medium">{error}</span>
          </div>
        )}

        {/* Dashboard Content */}
        {!hasRun && !loading && !error ? (
          <div className="bg-white/50 backdrop-blur-md border border-white/50 rounded-3xl p-16 text-center shadow-2xl shadow-indigo-100/40 transform transition-all hover:scale-[1.01]">
            <div className="bg-gradient-to-br from-indigo-100 to-violet-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
              <AlertCircle className="w-10 h-10 text-indigo-500" />
            </div>
            <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-700 mb-3">No reconciliation run available</h2>
            <p className="text-slate-500 text-lg max-w-md mx-auto">Run your first reconciliation to unlock insights, track exceptions, and monitor financial health.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* KPI Cards */}
            <KpiCards 
              summary={currentSummary as any} 
              valueReconciled={finance ? finance.expected_settlement - finance.unreconciled_value : 0} 
            />

            {/* Health & Finance */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <ReconciliationHealth 
                summary={currentSummary as any}
                manualReviewCount={exceptions?.exceptions.filter(e => e.status === "REVIEW").length || 0}
              />
              <FinancialSummary finance={finance} />
            </div>

            {/* Cash Position & Forecast */}
            <div className="grid grid-cols-1 gap-6">
              <CashPositionPanel position={cashPosition} />
              <CashForecastPanel forecast={cashForecast} />
            </div>

            {/* Exceptions */}
            <div className="flex justify-between items-center mt-8">
              <h3 className="text-lg font-bold text-slate-900">Exception Analytics</h3>
              <a 
                href="/exceptions" 
                className="text-sm font-medium text-amber-600 hover:text-amber-700 flex items-center bg-amber-50 hover:bg-amber-100 px-4 py-2 rounded-lg transition-colors"
              >
                View Exception Workbench <ArrowRight className="w-4 h-4 ml-2" />
              </a>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mt-4">
              <ExceptionAnalytics exceptionsData={exceptions} />
              <RecentExceptions exceptionsData={exceptions} />
            </div>
          </div>
        )}

        {/* Always show Benchmark Panel */}
        <div className="pt-6">
          <BenchmarkPanel benchmark={benchmark} />
        </div>

      </div>

      {/* Finance Copilot floating widget */}
      <FinanceCopilot hasRun={hasRun} />
    </div>
  );
}
