import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { ExceptionListResponse } from "@/services/api";
import { formatINR } from "@/lib/utils";

export function ExceptionAnalytics({
  exceptionsData,
}: {
  exceptionsData: ExceptionListResponse | null;
}) {
  if (!exceptionsData || exceptionsData.total_exceptions === 0) {
    return (
      <Card className="col-span-2">
        <CardHeader>
          <CardTitle>Exception Analytics</CardTitle>
        </CardHeader>
        <CardContent className="h-48 flex items-center justify-center text-slate-400">
          No exceptions to analyze.
        </CardContent>
      </Card>
    );
  }

  // Aggregate exceptions by type
  const typeMap: Record<string, { count: number; amount: number }> = {};
  
  exceptionsData.exceptions.forEach((exc) => {
    if (!typeMap[exc.type]) {
      typeMap[exc.type] = { count: 0, amount: 0 };
    }
    typeMap[exc.type].count += 1;
    typeMap[exc.type].amount += exc.amount;
  });

  const sortedTypes = Object.entries(typeMap).sort(
    (a, b) => b[1].count - a[1].count
  );
  
  const totalExceptions = exceptionsData.total_exceptions;

  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle>Exception Analytics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {sortedTypes.map(([type, data]) => {
            const percentage = (data.count / totalExceptions) * 100;
            return (
              <div key={type} className="flex flex-col space-y-1">
                <div className="flex justify-between text-sm font-medium">
                  <span className="text-slate-800">{type}</span>
                  <div className="flex space-x-4">
                    <span className="text-slate-500">{data.count} cases</span>
                    <span className="text-slate-900">{formatINR(data.amount)}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-amber-500 rounded-full"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-500 w-8 text-right">
                    {percentage.toFixed(0)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
