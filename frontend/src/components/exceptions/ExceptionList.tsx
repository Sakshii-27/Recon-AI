import { formatINR, cn } from "@/lib/utils";
import { ExceptionDetail } from "@/services/api";

export function ExceptionList({
  exceptions,
  selectedId,
  onSelect,
}: {
  exceptions: ExceptionDetail[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  if (exceptions.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto p-6 flex flex-col items-center justify-center text-slate-400">
        <p className="text-sm font-medium">No matching exceptions</p>
        <p className="text-xs mt-1">Try changing your search or filters.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="divide-y divide-slate-100">
        {exceptions.map((exc) => {
          const isSelected = exc.id === selectedId;
          
          let statusColor = "bg-slate-100 text-slate-600 border-slate-200";
          let statusDot = "bg-slate-400";
          
          if (exc.status === "REVIEW") {
            statusColor = "bg-amber-50 text-amber-700 border-amber-200";
            statusDot = "bg-amber-500";
          } else if (exc.status === "RESOLVED") {
            statusColor = "bg-green-50 text-green-700 border-green-200";
            statusDot = "bg-green-500";
          } else if (exc.status === "CRITICAL" || exc.status === "UNRESOLVED") {
            statusColor = "bg-red-50 text-red-700 border-red-200";
            statusDot = "bg-red-500";
          }

          return (
            <button
              key={exc.id}
              onClick={() => onSelect(exc.id)}
              className={cn(
                "w-full text-left p-4 hover:bg-slate-100 transition-colors focus:outline-none focus:bg-slate-100",
                isSelected ? "bg-blue-50/50 hover:bg-blue-50/80 border-l-4 border-l-blue-600" : "border-l-4 border-l-transparent"
              )}
            >
              <div className="flex justify-between items-start mb-1">
                <span className="text-xs font-mono text-slate-500 truncate mr-2" title={exc.id}>
                  {exc.id.split("-").slice(-2).join("-")}
                </span>
                <span className={cn("text-[10px] px-2 py-0.5 rounded-full border flex items-center shadow-sm", statusColor)}>
                  <span className={cn("w-1.5 h-1.5 rounded-full mr-1.5", statusDot)}></span>
                  {exc.status}
                </span>
              </div>
              <div className="font-medium text-slate-900 truncate mb-1" title={exc.type}>
                {exc.type}
              </div>
              <div className="text-sm font-semibold text-slate-700">
                {formatINR(exc.amount)}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
