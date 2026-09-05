import { Database, CreditCard, Landmark, XCircle, CheckCircle } from "lucide-react";
import { formatINR } from "@/lib/utils";

export function EvidenceComparison({ evidence }: { evidence: any }) {
  const erp = evidence.erp_evidence || [];
  const gateway = evidence.gateway_evidence || [];
  const bank = evidence.bank_evidence || [];

  return (
    <div className="flex flex-col space-y-4">
      <EvidenceCard 
        title="ERP / OMS" 
        icon={<Database className="w-4 h-4 text-slate-500" />}
        data={erp} 
        emptyMsg="No ERP record found" 
        borderColor="border-blue-200"
        headerBg="bg-blue-50/50"
      />
      <EvidenceCard 
        title="Payment Gateway" 
        icon={<CreditCard className="w-4 h-4 text-slate-500" />}
        data={gateway} 
        emptyMsg="No Gateway record found" 
        borderColor="border-purple-200"
        headerBg="bg-purple-50/50"
      />
      <EvidenceCard 
        title="Bank Statement" 
        icon={<Landmark className="w-4 h-4 text-slate-500" />}
        data={bank} 
        emptyMsg="No Bank record found" 
        borderColor="border-emerald-200"
        headerBg="bg-emerald-50/50"
      />
    </div>
  );
}

function EvidenceCard({ 
  title, 
  icon, 
  data, 
  emptyMsg,
  borderColor,
  headerBg
}: { 
  title: string; 
  icon: React.ReactNode; 
  data: any[]; 
  emptyMsg: string;
  borderColor: string;
  headerBg: string;
}) {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-red-200 bg-red-50/50 p-6 flex flex-col items-center justify-center text-red-500">
        <XCircle className="w-6 h-6 mb-2 opacity-50" />
        <span className="text-sm font-medium">{emptyMsg}</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-3">
      {data.map((record, idx) => (
        <div key={idx} className={`rounded-xl border ${borderColor} bg-white shadow-sm overflow-hidden`}>
          <div className={`${headerBg} px-4 py-2 flex items-center border-b ${borderColor}`}>
            {icon}
            <span className="ml-2 text-sm font-semibold text-slate-900">{title}</span>
            {data.length > 1 && (
              <span className="ml-2 text-xs font-medium text-slate-500">Record {idx + 1}</span>
            )}
          </div>
          <div className="p-4 bg-slate-50">
            <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
              {Object.entries(record).map(([key, value]) => {
                // Formatting for display
                const displayKey = key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                let displayValue = String(value);
                
                // Try to format currency fields if they look like amounts
                if (typeof value === "number" && (key.includes("amount") || key.includes("fee") || key.includes("gst") || key.includes("total") || key.includes("value"))) {
                  displayValue = formatINR(value);
                } else if (value === null || value === undefined) {
                  displayValue = "-";
                }

                return (
                  <div key={key} className="flex flex-col">
                    <dt className="text-xs font-medium text-slate-500 mb-0.5 truncate" title={displayKey}>{displayKey}</dt>
                    <dd className="text-slate-900 font-mono text-xs break-all bg-white px-2 py-1 border border-slate-100 rounded">{displayValue}</dd>
                  </div>
                );
              })}
            </dl>
          </div>
        </div>
      ))}
    </div>
  );
}
