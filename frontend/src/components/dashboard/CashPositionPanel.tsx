import { formatINR } from "@/lib/utils";
import { Wallet, CheckCircle, Clock, AlertTriangle, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

export function CashPositionPanel({ position }: { position: any }) {
  if (!position) return null;

  return (
    <div className="bg-white/40 backdrop-blur-md border border-white/60 shadow-lg shadow-indigo-100/20 p-6 rounded-2xl flex flex-col h-full col-span-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-gradient-to-br from-emerald-100 to-teal-100 text-emerald-600 rounded-lg shadow-sm">
            <Wallet className="w-5 h-5" />
          </div>
          <h2 className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-700 tracking-tight">Cash Position</h2>
        </div>
        <span className="text-xs font-semibold px-3 py-1.5 bg-emerald-50 border border-emerald-100/50 text-emerald-700 rounded-lg shadow-sm">
          {position.reconciliation_coverage.toFixed(2)}% Reconciled
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Actual Cash */}
        <div className="p-5 rounded-2xl border border-emerald-200/50 bg-gradient-to-br from-emerald-50/50 to-emerald-100/30 hover:-translate-y-1 hover:shadow-lg hover:shadow-emerald-100/40 transition-all duration-300">
          <div className="flex items-center space-x-2 text-emerald-600 mb-3">
            <CheckCircle className="w-4 h-4" />
            <h3 className="text-xs font-bold uppercase tracking-wider">Actual Bank Cash</h3>
          </div>
          <p className="text-2xl font-extrabold text-emerald-900 tracking-tight">{formatINR(position.bank_cash)}</p>
          <p className="text-xs text-emerald-600/80 mt-1 font-medium bg-emerald-50/50 inline-block px-2 py-0.5 rounded">Verified by bank statement</p>
        </div>

        {/* Expected Cash */}
        <div className="p-5 rounded-2xl border border-slate-200/50 bg-gradient-to-br from-slate-50/50 to-slate-100/30 hover:-translate-y-1 hover:shadow-lg hover:shadow-slate-200/40 transition-all duration-300">
          <div className="flex items-center space-x-2 text-slate-500 mb-3">
            <Wallet className="w-4 h-4" />
            <h3 className="text-xs font-bold uppercase tracking-wider">Expected Gateway Cash</h3>
          </div>
          <p className="text-2xl font-extrabold text-slate-800 tracking-tight">{formatINR(position.gateway_net_expected)}</p>
          <p className="text-xs text-slate-500 mt-1 font-medium bg-slate-100/50 inline-block px-2 py-0.5 rounded">Captured net of MDR & GST</p>
        </div>

        {/* Pending Cash */}
        <div className="p-5 rounded-2xl border border-amber-200/50 bg-gradient-to-br from-amber-50/50 to-amber-100/30 hover:-translate-y-1 hover:shadow-lg hover:shadow-amber-100/40 transition-all duration-300">
          <div className="flex items-center space-x-2 text-amber-600 mb-3">
            <Clock className="w-4 h-4" />
            <h3 className="text-xs font-bold uppercase tracking-wider">Pending Settlement</h3>
          </div>
          <p className="text-2xl font-extrabold text-amber-900 tracking-tight">{formatINR(position.pending_settlement)}</p>
          <p className="text-xs text-amber-700/80 mt-1 font-medium bg-amber-50/50 inline-block px-2 py-0.5 rounded">Gateway confirmed, missing from bank</p>
        </div>

        {/* At Risk Cash */}
        <div className="p-5 rounded-2xl border border-rose-200/50 bg-gradient-to-br from-rose-50/50 to-rose-100/30 hover:-translate-y-1 hover:shadow-lg hover:shadow-rose-100/40 transition-all duration-300">
          <div className="flex items-center space-x-2 text-rose-600 mb-3">
            <TrendingDown className="w-4 h-4" />
            <h3 className="text-xs font-bold uppercase tracking-wider">Cash At Risk</h3>
          </div>
          <p className="text-2xl font-extrabold text-rose-900 tracking-tight">{formatINR(position.cash_at_risk)}</p>
          <p className="text-xs text-rose-600/80 mt-1 font-medium bg-rose-50/50 inline-block px-2 py-0.5 rounded">
            Out of {formatINR(position.exception_value)} total exceptions
          </p>
        </div>
      </div>
    </div>
  );
}
