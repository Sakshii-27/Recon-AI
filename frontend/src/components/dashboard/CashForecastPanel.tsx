import { formatINR } from "@/lib/utils";
import { TrendingUp, Calendar, Info } from "lucide-react";

export function CashForecastPanel({ forecast }: { forecast: any }) {
  if (!forecast || !forecast.forecast_7_day || forecast.forecast_7_day.length === 0) return null;

  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col h-full col-span-full">
      <div className="flex items-center space-x-2 mb-6">
        <TrendingUp className="w-5 h-5 text-indigo-600" />
        <h2 className="text-lg font-bold text-slate-900">7-Day Deterministic Cash Forecast</h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 rounded-tl-lg">Date</th>
              <th className="px-4 py-3">Expected Inflow</th>
              <th className="px-4 py-3">Cumulative</th>
              <th className="px-4 py-3">Confidence</th>
              <th className="px-4 py-3 rounded-tr-lg">Basis</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {forecast.forecast_7_day.map((day: any, idx: number) => (
              <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                <td className="px-4 py-3 font-medium text-slate-900 flex items-center">
                  <Calendar className="w-4 h-4 mr-2 text-slate-400" />
                  {day.date}
                </td>
                <td className="px-4 py-3 text-emerald-700 font-medium">
                  {day.expected_inflow > 0 ? `+${formatINR(day.expected_inflow)}` : "-"}
                </td>
                <td className="px-4 py-3 font-semibold text-slate-700">
                  {formatINR(day.cumulative_expected_cash)}
                </td>
                <td className="px-4 py-3">
                  {day.confidence === "HIGH" ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                      HIGH
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
                      N/A
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-xs text-slate-500">
                  <div className="flex items-center">
                    {day.basis === "deterministic_expected_settlement" ? (
                      <span className="truncate max-w-[200px]" title="Explicit settlement date from gateway/generator">
                        Deterministic Settlement
                      </span>
                    ) : (
                      <span className="italic text-slate-400">No scheduled settlements</span>
                    )}
                    <Info className="w-3 h-3 ml-1.5 text-slate-300" />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 text-xs text-slate-500 flex items-start">
        <Info className="w-4 h-4 mr-1.5 text-indigo-400 flex-shrink-0" />
        <p>
          <strong>High confidence</strong> means the settlement date is explicitly available in the deterministic dataset; 
          it does not represent a statistically calibrated probability. Cash forecasts are derived safely without LLMs.
        </p>
      </div>
    </div>
  );
}
