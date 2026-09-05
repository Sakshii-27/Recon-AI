import { ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { ExceptionListResponse } from "@/services/api";
import { formatINR } from "@/lib/utils";

export function RecentExceptions({
  exceptionsData,
}: {
  exceptionsData: ExceptionListResponse | null;
}) {
  if (!exceptionsData || exceptionsData.total_exceptions === 0) {
    return (
      <Card className="col-span-2">
        <CardHeader>
          <CardTitle>Recent Exceptions</CardTitle>
        </CardHeader>
        <CardContent className="h-48 flex items-center justify-center text-slate-400">
          No exceptions found.
        </CardContent>
      </Card>
    );
  }

  // Take the first 5 exceptions
  const recent = exceptionsData.exceptions.slice(0, 5);

  return (
    <Card className="col-span-2 flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Exceptions</CardTitle>
        <button
          disabled
          className="text-sm font-medium text-slate-400 flex items-center hover:text-slate-600 transition-colors"
        >
          View All <ArrowRight className="w-4 h-4 ml-1" />
        </button>
      </CardHeader>
      <CardContent className="flex-1">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-y border-slate-100">
              <tr>
                <th className="px-4 py-3 font-medium">ID</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium text-right">Amount</th>
                <th className="px-4 py-3 font-medium text-center">Status</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((exc) => {
                let statusColor = "bg-amber-100 text-amber-800";
                if (exc.status === "RESOLVED") {
                  statusColor = "bg-green-100 text-green-800";
                } else if (exc.status === "CRITICAL" || exc.status === "UNRESOLVED") {
                  statusColor = "bg-red-100 text-red-800";
                }

                return (
                  <tr key={exc.id} className="border-b border-slate-100 hover:bg-slate-50/50">
                    <td className="px-4 py-3 font-medium text-slate-900 truncate max-w-[120px]" title={exc.id}>
                      {exc.id.split("-").slice(-2).join("-")}
                    </td>
                    <td className="px-4 py-3 text-slate-600 truncate max-w-[150px]" title={exc.type}>
                      {exc.type}
                    </td>
                    <td className="px-4 py-3 text-slate-900 font-medium text-right">
                      {formatINR(exc.amount)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${statusColor}`}>
                        {exc.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {exceptionsData.total_exceptions > 5 && (
          <div className="text-xs text-slate-500 mt-4 text-center">
            Showing 5 of {exceptionsData.total_exceptions} exceptions
          </div>
        )}
      </CardContent>
    </Card>
  );
}
