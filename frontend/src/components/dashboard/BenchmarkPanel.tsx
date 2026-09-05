import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { BenchmarkBaselineResponse } from "@/services/api";

export function BenchmarkPanel({
  benchmark,
}: {
  benchmark: BenchmarkBaselineResponse | null;
}) {
  if (!benchmark || !benchmark.baseline || Object.keys(benchmark.baseline).length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Deterministic Baseline</CardTitle>
        </CardHeader>
        <CardContent className="h-48 flex items-center justify-center text-slate-400">
          No benchmark data available.
        </CardContent>
      </Card>
    );
  }

  // Sort keys numerically
  const sizes = Object.keys(benchmark.baseline).sort((a, b) => parseInt(a) - parseInt(b));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Deterministic Baseline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-y border-slate-100">
              <tr>
                <th className="px-4 py-3 font-medium">Records</th>
                <th className="px-4 py-3 font-medium">Precision</th>
                <th className="px-4 py-3 font-medium">Recall</th>
                <th className="px-4 py-3 font-medium">F1</th>
                <th className="px-4 py-3 font-medium">Match Rate</th>
              </tr>
            </thead>
            <tbody>
              {sizes.map((size) => {
                const b = benchmark.baseline[size];
                return (
                  <tr key={size} className="border-b border-slate-100 hover:bg-slate-50/50">
                    <td className="px-4 py-3 font-medium text-slate-900">{size}</td>
                    <td className="px-4 py-3 text-slate-600">{(b.precision * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-slate-600">{(b.recall * 100).toFixed(0)}%</td>
                    <td className="px-4 py-3 text-slate-600">{(b.f1 * 100).toFixed(2)}%</td>
                    <td className="px-4 py-3 text-slate-900 font-medium">{(b.match_rate * 100).toFixed(2)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
