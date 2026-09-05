import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { ReconciliationSummary } from "@/services/api";

export function ReconciliationHealth({
  summary,
  manualReviewCount,
}: {
  summary: ReconciliationSummary | null;
  manualReviewCount: number;
}) {
  const cardStyle = "bg-white/40 backdrop-blur-md border border-white/60 shadow-lg shadow-indigo-100/20 hover:shadow-xl hover:shadow-indigo-100/40 transition-all duration-300 rounded-2xl col-span-2";

  if (!summary) {
    return (
      <Card className={cardStyle}>
        <CardHeader>
          <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Reconciliation Health</CardTitle>
        </CardHeader>
        <CardContent className="h-48 flex items-center justify-center text-slate-400">
          No data available.
        </CardContent>
      </Card>
    );
  }

  const safeAutoCount = summary.matched; // Since all matched in deterministic are autonomous

  return (
    <Card className={cardStyle}>
      <CardHeader>
        <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Reconciliation Health</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div className="flex flex-col space-y-3">
            <div className="flex justify-between items-center font-medium">
              <span className="text-slate-600 text-sm">Match Progress</span>
              <span className="text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-100">{summary.match_rate.toFixed(2)}%</span>
            </div>
            <div className="h-4 w-full bg-slate-200/50 rounded-full overflow-hidden flex shadow-inner">
              <div
                className="h-full bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full shadow-[0_0_10px_rgba(52,211,153,0.5)] transition-all duration-1000 ease-out"
                style={{ width: `${summary.match_rate}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-y-5 gap-x-8 text-sm">
            <div className="flex justify-between items-center border-b border-slate-200/50 pb-2">
              <span className="text-slate-500 font-medium">Matched</span>
              <span className="font-bold text-slate-800 bg-slate-100 px-2 py-0.5 rounded-md">{summary.matched}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-200/50 pb-2">
              <span className="text-slate-500 font-medium">Safe Autonomous (Batch)</span>
              <span className="font-bold text-emerald-700 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-md shadow-sm">{safeAutoCount}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-200/50 pb-2">
              <span className="text-slate-500 font-medium">Exceptions</span>
              <span className="font-bold text-rose-700 bg-rose-50 border border-rose-100 px-2 py-0.5 rounded-md shadow-sm">{summary.exceptions}</span>
            </div>
            <div className="flex justify-between items-center border-b border-slate-200/50 pb-2">
              <span className="text-slate-500 font-medium">Manual Review</span>
              <span className="font-bold text-amber-700 bg-amber-50 border border-amber-100 px-2 py-0.5 rounded-md shadow-sm">{manualReviewCount}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
