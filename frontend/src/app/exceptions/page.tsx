"use client";

import { useEffect, useState } from "react";
import { ArrowLeft, Search, Bot } from "lucide-react";
import { fetchExceptions, fetchException, ExceptionListResponse, ExceptionDetail } from "@/services/api";
import { ExceptionList } from "@/components/exceptions/ExceptionList";
import { ExceptionDetailPanel } from "@/components/exceptions/ExceptionDetail";
import { ExceptionFilters } from "@/components/exceptions/ExceptionFilters";

export default function ExceptionWorkbench() {
  const [exceptions, setExceptions] = useState<ExceptionListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedExceptionId, setSelectedExceptionId] = useState<string | null>(null);

  // Filter state
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  const [sortOrder, setSortOrder] = useState("Highest Amount");

  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetchExceptions();
        setExceptions(data);
      } catch (err: any) {
        if (err.message.includes("Failed to fetch exceptions") || err.message.includes("Not Found")) {
          setExceptions(null); // No run
        } else {
          setError(err.message || "Failed to load exceptions.");
        }
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <span className="text-slate-500 font-medium">Loading Exception Workbench...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 p-6 flex flex-col items-center justify-center">
        <h2 className="text-xl font-bold text-red-600 mb-2">Unable to load exceptions</h2>
        <p className="text-slate-600 mb-6">{error}</p>
        <a href="/" className="text-slate-900 bg-white border border-slate-200 px-4 py-2 rounded-lg font-medium hover:bg-slate-50 transition-colors">
          Return to Dashboard
        </a>
      </div>
    );
  }

  if (!exceptions || exceptions.total_exceptions === 0) {
    return (
      <div className="min-h-screen bg-slate-50 p-6 flex flex-col items-center pt-24">
        <h2 className="text-xl font-bold text-slate-900 mb-2">No Exceptions</h2>
        <p className="text-slate-500 mb-6 max-w-md text-center">
          The latest reconciliation run has no outstanding exceptions, or a run has not been executed yet.
        </p>
        <a href="/" className="text-white bg-slate-900 px-4 py-2 rounded-lg font-medium hover:bg-slate-800 transition-colors">
          Back to Dashboard
        </a>
      </div>
    );
  }

  // Derive unique types and statuses
  const availableTypes = Array.from(new Set(exceptions.exceptions.map((e) => e.type)));
  const availableStatuses = Array.from(new Set(exceptions.exceptions.map((e) => e.status)));

  // Filter & Sort
  let filtered = exceptions.exceptions.filter((exc) => {
    const matchSearch = exc.id.toLowerCase().includes(searchTerm.toLowerCase()) || 
                        exc.type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchType = typeFilter === "All" || exc.type === typeFilter;
    const matchStatus = statusFilter === "All" || exc.status === statusFilter;
    return matchSearch && matchType && matchStatus;
  });

  filtered.sort((a, b) => {
    if (sortOrder === "Highest Amount") return b.amount - a.amount;
    if (sortOrder === "Lowest Amount") return a.amount - b.amount;
    return 0;
  });

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col h-screen overflow-hidden font-sans">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between flex-shrink-0 z-10">
        <div className="flex items-center space-x-4">
          <a href="/" className="text-slate-400 hover:text-slate-700 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </a>
          <div>
            <h1 className="text-lg font-bold text-slate-900 leading-tight">Exception Workbench</h1>
            <p className="text-xs font-medium text-slate-500">Investigate reconciliation exceptions and financial impact</p>
          </div>
        </div>
        <div className="flex items-center space-x-2 bg-green-50 px-3 py-1 rounded-full border border-green-100">
          <div className="w-2 h-2 rounded-full bg-green-500"></div>
          <span className="text-xs font-semibold text-green-700 uppercase tracking-wider">Operational</span>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Pane: List */}
        <div className="w-1/3 min-w-[320px] max-w-sm flex flex-col bg-slate-50 border-r border-slate-200 z-0">
          <ExceptionFilters 
            searchTerm={searchTerm} setSearchTerm={setSearchTerm}
            typeFilter={typeFilter} setTypeFilter={setTypeFilter} availableTypes={availableTypes}
            statusFilter={statusFilter} setStatusFilter={setStatusFilter} availableStatuses={availableStatuses}
            sortOrder={sortOrder} setSortOrder={setSortOrder}
          />
          <ExceptionList 
            exceptions={filtered} 
            selectedId={selectedExceptionId} 
            onSelect={setSelectedExceptionId} 
          />
        </div>

        {/* Right Pane: Detail */}
        <div className="flex-1 overflow-y-auto bg-white p-6 relative">
          {selectedExceptionId ? (
            <ExceptionDetailPanel exceptionId={selectedExceptionId} />
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-4">
              <Search className="w-12 h-12 opacity-20" />
              <p className="text-sm font-medium">Select an exception from the list to investigate</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
