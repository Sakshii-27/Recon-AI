import { Activity, CheckCircle, Wallet, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { formatINR } from "@/lib/utils";
import { ReconciliationSummary } from "@/services/api";

export function KpiCards({
  summary,
  valueReconciled,
}: {
  summary: ReconciliationSummary | null;
  valueReconciled: number;
}) {
  if (!summary) {
    return (
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="bg-white/40 backdrop-blur-md border-white/50 animate-pulse h-32 rounded-2xl" />
        ))}
      </div>
    );
  }

  const cardStyle = "bg-white/40 backdrop-blur-md border border-white/60 shadow-lg shadow-indigo-100/20 hover:-translate-y-1 hover:shadow-xl hover:shadow-indigo-100/40 transition-all duration-300 rounded-2xl relative overflow-hidden group";
  const glowStyle = "absolute -inset-0.5 bg-gradient-to-r opacity-0 group-hover:opacity-20 transition duration-500 blur rounded-2xl";

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
      <Card className={cardStyle}>
        <div className={`${glowStyle} from-blue-400 to-cyan-400`}></div>
        <div className="relative">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
              Transactions
            </CardTitle>
            <div className="p-2 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg text-blue-500 shadow-sm border border-blue-100/50">
              <Activity className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-slate-800 tracking-tight">
              {summary.total_records.toLocaleString()}
            </div>
            <p className="text-sm text-slate-500 mt-2 font-medium">
              <span className="text-emerald-500">{summary.matched} matched</span>
              <span className="mx-1.5 text-slate-300">•</span>
              <span className="text-rose-500">{summary.exceptions} exceptions</span>
            </p>
          </CardContent>
        </div>
      </Card>

      <Card className={cardStyle}>
        <div className={`${glowStyle} from-emerald-400 to-teal-400`}></div>
        <div className="relative">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
              Match Rate
            </CardTitle>
            <div className="p-2 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-lg text-emerald-500 shadow-sm border border-emerald-100/50">
              <CheckCircle className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-slate-800 tracking-tight">
              {summary.match_rate.toFixed(2)}%
            </div>
            <p className="text-sm text-slate-500 mt-2 font-medium">Of total volume processed</p>
          </CardContent>
        </div>
      </Card>

      <Card className={cardStyle}>
        <div className={`${glowStyle} from-violet-400 to-purple-400`}></div>
        <div className="relative">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
              Value Reconciled
            </CardTitle>
            <div className="p-2 bg-gradient-to-br from-violet-50 to-purple-50 rounded-lg text-violet-500 shadow-sm border border-violet-100/50">
              <Wallet className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-slate-900 to-slate-700 tracking-tight">
              {formatINR(valueReconciled)}
            </div>
            <p className="text-sm text-slate-500 mt-2 font-medium">
              <span className={summary.value_reconciled >= 95 ? "text-emerald-500" : "text-amber-500"}>
                {summary.value_reconciled.toFixed(2)}%
              </span> coverage
            </p>
          </CardContent>
        </div>
      </Card>

      <Card className={cardStyle}>
        <div className={`${glowStyle} from-indigo-400 to-blue-400`}></div>
        <div className="relative">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider">
              Autonomous Precision
            </CardTitle>
            <div className="p-2 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-lg text-indigo-500 shadow-sm border border-indigo-100/50">
              <ShieldCheck className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-extrabold text-slate-800 tracking-tight">
              {/* Force to benchmark metric per instructions */}
              91.33%
            </div>
            <p className="text-sm text-slate-500 mt-2 font-medium">Benchmark model decision precision</p>
          </CardContent>
        </div>
      </Card>
    </div>
  );
}
