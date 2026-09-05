import { TrendingDown, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { FinancialSummaryResponse } from "@/services/api";
import { formatINR } from "@/lib/utils";

export function FinancialSummary({
  finance,
}: {
  finance: FinancialSummaryResponse | null;
}) {
  const cardStyle = "bg-white/40 backdrop-blur-md border border-white/60 shadow-lg shadow-indigo-100/20 hover:shadow-xl hover:shadow-indigo-100/40 transition-all duration-300 rounded-2xl col-span-2";

  if (!finance) {
    return (
      <Card className={cardStyle}>
        <CardHeader>
          <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Financial Summary</CardTitle>
        </CardHeader>
        <CardContent className="h-48 flex items-center justify-center text-slate-400">
          No data available.
        </CardContent>
      </Card>
    );
  }

  const variance = finance.bank_settlement - finance.expected_settlement;
  const isPositiveVariance = variance > 0;
  const isNegativeVariance = variance < 0;

  return (
    <Card className={cardStyle}>
      <CardHeader>
        <CardTitle className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Financial Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <p className="text-sm text-slate-500 font-medium mb-1">Expected Settlement</p>
              <p className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-slate-900 to-slate-700">
                {formatINR(finance.expected_settlement)}
              </p>
            </div>
            
            <div className="pt-4 border-t border-slate-200/50">
              <p className="text-sm text-slate-500 font-medium mb-1">Actual Settlement</p>
              <p className="text-2xl font-extrabold text-slate-800">
                {formatINR(finance.bank_settlement)}
              </p>
            </div>
          </div>

          <div className={`rounded-xl p-5 flex flex-col justify-center border shadow-inner ${
            isNegativeVariance 
              ? "bg-gradient-to-br from-rose-50 to-red-50 border-red-100" 
              : isPositiveVariance 
              ? "bg-gradient-to-br from-amber-50 to-orange-50 border-amber-100"
              : "bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200"
          }`}>
            <p className="text-sm text-slate-600 font-medium mb-2">Variance</p>
            <div className="flex items-center space-x-2">
              {isNegativeVariance ? (
                <div className="p-1.5 bg-red-100 text-red-600 rounded-md shadow-sm">
                  <TrendingDown className="h-5 w-5" />
                </div>
              ) : isPositiveVariance ? (
                <div className="p-1.5 bg-amber-100 text-amber-600 rounded-md shadow-sm">
                  <TrendingUp className="h-5 w-5" />
                </div>
              ) : null}
              <p
                className={`text-2xl font-extrabold ${
                  isNegativeVariance
                    ? "text-red-600"
                    : isPositiveVariance
                    ? "text-amber-600"
                    : "text-slate-700"
                }`}
              >
                {formatINR(Math.abs(variance))}
              </p>
            </div>
            <p className="text-xs text-slate-500 mt-3 font-medium bg-white/50 inline-block px-2 py-1 rounded">
              {isNegativeVariance
                ? "Shortfall against expected"
                : isPositiveVariance
                ? "Overage against expected"
                : "Perfectly matched"}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
