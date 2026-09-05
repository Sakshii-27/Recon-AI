import { useEffect, useState } from "react";
import { fetchException, ExceptionDetail, investigateWithAIV2 } from "@/services/api";
import { formatINR, cn } from "@/lib/utils";
import { 
  AlertTriangle, 
  TrendingDown, 
  Bot, 
  FileSearch, 
  Sparkles, 
  ShieldAlert, 
  CheckCircle2, 
  ArrowRight, 
  RefreshCw,
  BookOpen,
  FileCheck,
  Search
} from "lucide-react";
import { EvidenceComparison } from "@/components/exceptions/EvidenceComparison";

export function ExceptionDetailPanel({ exceptionId }: { exceptionId: string }) {
  const [detail, setDetail] = useState<ExceptionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [aiResult, setAiResult] = useState<any>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [executionTime, setExecutionTime] = useState<number | null>(null);

  useEffect(() => {
    async function loadDetail() {
      setLoading(true);
      setError(null);
      setAiResult(null);
      setAiError(null);
      setExecutionTime(null);
      try {
        const data = await fetchException(exceptionId);
        setDetail(data);
      } catch (err: any) {
        setError(err.message || "Failed to load exception details.");
      } finally {
        setLoading(false);
      }
    }
    loadDetail();
  }, [exceptionId]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400">
        <span className="text-sm font-medium animate-pulse">Loading exception details...</span>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-500">
        <AlertTriangle className="w-10 h-10 text-amber-500 mb-2 opacity-50" />
        <p className="text-sm font-medium">{error || "Exception not found"}</p>
        <p className="text-xs mt-1 text-center max-w-xs">
          This exception may no longer exist in the current reconciliation run.
        </p>
      </div>
    );
  }

  const isAiEligible = ["DUPLICATE", "BATCH_SETTLEMENT", "MISSING_ERP"].includes(detail.type);

  const handleAiInvestigation = async () => {
    setAiLoading(true);
    setAiError(null);
    const startTime = performance.now();
    try {
      const result = await investigateWithAIV2(exceptionId);
      const durationSec = Math.round((performance.now() - startTime) / 100) / 10;
      setExecutionTime(durationSec);
      setAiResult(result);
    } catch (err: any) {
      setAiError(err.message || "AI investigation failed.");
    } finally {
      setAiLoading(false);
    }
  };

  // Deterministic explanation logic
  let explanation = "The deterministic engine could not safely resolve this transaction footprint automatically.";
  if (detail.type === "MISSING_ERP") {
    explanation = "A gateway transaction was captured, but no corresponding ERP order exists in the source accounting system.";
  } else if (detail.type === "MISSING_BANK") {
    explanation = "An ERP order and Gateway capture exist, but the funds have not settled in the Bank.";
  } else if (detail.type === "DUPLICATE") {
    explanation = "Multiple conflicting records map to the same transaction footprint, preventing a deterministic 1:1 match.";
  } else if (detail.type === "BATCH_SETTLEMENT") {
    explanation = "The bank settled a bulk amount, but the individual gateway transactions could not be isolated deterministically.";
  } else if (detail.type === "FEE_ANOMALY") {
    explanation = "The fees charged by the gateway do not match the expected contractual MDR/GST rates.";
  }

  const hasVariance = detail.difference > 0;

  return (
    <div className="flex flex-col space-y-6 pb-12">
      {/* 1. Top Header & Identity Card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <span className="px-2.5 py-0.5 rounded bg-slate-100 text-slate-800 text-xs font-semibold uppercase tracking-wider border border-slate-200">
                {detail.type.replace(/_/g, " ")}
              </span>
              <span className="text-sm font-mono text-slate-500 font-medium">
                {detail.id}
              </span>
              <span className={cn(
                "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border",
                detail.status === "REVIEW" ? "bg-amber-50 text-amber-700 border-amber-200" :
                detail.status === "RESOLVED" ? "bg-green-50 text-green-700 border-green-200" :
                "bg-red-50 text-red-700 border-red-200"
              )}>
                {detail.status}
              </span>
            </div>
            
            <div className="flex items-baseline space-x-3">
              <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
                {formatINR(detail.amount)}
              </h2>
              {hasVariance && (
                <div className="flex items-center text-rose-700 bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-md text-xs font-semibold">
                  <TrendingDown className="w-3.5 h-3.5 mr-1 text-rose-600" />
                  Variance: {formatINR(detail.difference)}
                </div>
              )}
            </div>
          </div>

          {/* AI Trigger Action or Ineligible Badge */}
          <div className="flex items-center space-x-3">
            {!aiResult && !aiLoading && (
              isAiEligible ? (
                <button
                  onClick={handleAiInvestigation}
                  className="inline-flex items-center px-5 py-2.5 rounded-lg text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm transition-all hover:shadow cursor-pointer"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Investigate with AI
                </button>
              ) : (
                <span className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium text-slate-500 bg-slate-100 border border-slate-200">
                  <Bot className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
                  Deterministic Engine Only
                </span>
              )
            )}

            {aiLoading && (
              <div className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-medium">
                <RefreshCw className="w-3.5 h-3.5 mr-2 animate-spin text-indigo-600" />
                Analyzing with AI (~4s)...
              </div>
            )}

            {aiResult && !aiLoading && (
              <button
                onClick={handleAiInvestigation}
                className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                Re-investigate
              </button>
            )}
          </div>
        </div>

        {/* Error Alert if AI failed */}
        {aiError && !aiLoading && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs flex items-center justify-between">
            <div className="flex items-center">
              <AlertTriangle className="w-4 h-4 mr-1.5 flex-shrink-0" />
              <span>{aiError}</span>
            </div>
            <button onClick={() => setAiError(null)} className="underline font-semibold ml-3 cursor-pointer">Dismiss</button>
          </div>
        )}
      </div>

      {/* 2. Executive AI Investigation Showcase (if triggered) */}
      {aiResult && !aiLoading && (
        <div className="bg-gradient-to-b from-indigo-50/70 via-white to-white border border-indigo-200/80 rounded-2xl p-6 shadow-sm space-y-6">
          
          {/* Header Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-indigo-100 gap-3">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-sm">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-base font-bold text-slate-900">AI Autonomous Investigation</h3>
                  {executionTime && (
                    <span className="text-[11px] font-medium text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200">
                      ⚡ {executionTime}s
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500">Evidence synthesis & independent risk validator audit</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="text-right">
                <div className="text-xs font-semibold text-slate-500">Recommendation</div>
                <span className={cn(
                  "inline-block px-3 py-1 rounded-lg text-xs font-bold tracking-wide uppercase border mt-0.5",
                  aiResult.decision === "HUMAN_REVIEW" ? "bg-amber-100 text-amber-900 border-amber-300" :
                  aiResult.decision === "INSUFFICIENT_EVIDENCE" ? "bg-slate-100 text-slate-800 border-slate-300" :
                  "bg-indigo-100 text-indigo-900 border-indigo-300"
                )}>
                  {aiResult.decision.replace(/_/g, " ")}
                </span>
              </div>
            </div>
          </div>

          {/* Fallback Warning if offline */}
          {aiResult.is_fallback && (
            <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-xs flex items-start space-x-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">AI Offline — Deterministic Fallback Preserved</span>
                <p className="mt-0.5 text-amber-800 text-[11px]">The AI service could not complete the multi-perspective pass. Deterministic transaction evidence is displayed below.</p>
              </div>
            </div>
          )}

          {/* Executive Verdict & Confidence Gauge */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex-1">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 block">
                  Executive Verdict
                </span>
                <p className="text-sm font-semibold text-slate-800 leading-relaxed">
                  {aiResult.reasoning}
                </p>
              </div>

              {/* Confidence Gauge */}
              <div className="w-full md:w-56 bg-slate-50 border border-slate-200 rounded-lg p-3 flex flex-col justify-center">
                <div className="flex justify-between items-center mb-1.5">
                  <span className="text-[11px] font-semibold text-slate-600">AI Confidence</span>
                  <span className="text-xs font-bold text-indigo-700">{Math.round(aiResult.confidence * 100)}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div 
                    className={cn(
                      "h-2 rounded-full transition-all duration-500",
                      aiResult.confidence < 0.6 ? "bg-amber-500" : "bg-indigo-600"
                    )} 
                    style={{ width: `${Math.round(aiResult.confidence * 100)}%` }}
                  />
                </div>
                <span className="text-[9px] text-slate-400 mt-1 block text-right italic">
                  Deterministic bounds preserved
                </span>
              </div>
            </div>
          </div>

          {/* Action Directive Callout */}
          <div className="bg-indigo-600 text-white rounded-xl p-4 shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-start space-x-3">
              <div className="p-2 rounded-lg bg-indigo-500/50 flex-shrink-0 mt-0.5">
                <ArrowRight className="w-4 h-4 text-white" />
              </div>
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-200 block">
                  Operator Next Action
                </span>
                <p className="text-sm font-semibold text-white mt-0.5 leading-snug">
                  {aiResult.recommended_action}
                </p>
              </div>
            </div>

            {aiResult.human_review_required && (
              <div className="flex-shrink-0">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase bg-indigo-950 text-indigo-200 border border-indigo-400/30">
                  <ShieldAlert className="w-3.5 h-3.5 mr-1.5 text-amber-300" />
                  Human Approval Mandatory
                </span>
              </div>
            )}
          </div>

          {/* 3 Investigation Pillars: Evidence, Risk Review, Policy & Precedent */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            {/* Pillar 1: Evidence Findings */}
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center space-x-2 text-slate-800 mb-2">
                  <FileCheck className="w-4 h-4 text-indigo-600" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">1. Evidence Analysis</h4>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {aiResult.evidence_analysis?.summary}
                </p>
              </div>

              {aiResult.evidence_analysis?.flags?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <span className="text-[10px] font-bold uppercase text-slate-400 block mb-1.5">Detected Footprints</span>
                  <div className="flex flex-col gap-1.5">
                    {aiResult.evidence_analysis.flags.map((flag: string, idx: number) => (
                      <div key={idx} className="flex items-start text-[11px] text-amber-800 bg-amber-50/70 border border-amber-200/60 rounded px-2 py-1">
                        <span className="mr-1.5 text-amber-600">•</span>
                        <span>{flag}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Pillar 2: Risk Validator Audit */}
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2 text-slate-800">
                    <ShieldAlert className="w-4 h-4 text-rose-600" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">2. Risk Validator</h4>
                  </div>
                  <span className={cn(
                    "text-[10px] font-bold px-2 py-0.5 rounded",
                    aiResult.risk_validation?.approved ? "bg-green-100 text-green-800" : "bg-rose-100 text-rose-800"
                  )}>
                    {aiResult.risk_validation?.approved ? "Approved" : "Scrutinized"}
                  </span>
                </div>

                {aiResult.risk_validation?.risk_concerns?.length > 0 ? (
                  <div className="space-y-1.5">
                    <span className="text-[10px] font-bold uppercase text-rose-500 block">Identified Skepticism / Contradictions:</span>
                    <ul className="space-y-1">
                      {aiResult.risk_validation.risk_concerns.map((rc: string, idx: number) => (
                        <li key={idx} className="text-[11px] text-rose-700 bg-rose-50/70 border border-rose-200/60 rounded px-2 py-1 leading-snug">
                          {rc}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p className="text-xs text-slate-600 leading-relaxed">
                    The independent Risk Validator found zero contradiction between the financial ledger and resolution proposal.
                  </p>
                )}
              </div>
            </div>

            {/* Pillar 3: Policy & Precedent */}
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center space-x-2 text-slate-800 mb-2">
                  <BookOpen className="w-4 h-4 text-teal-600" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">3. Policy & Precedents</h4>
                </div>

                {aiResult.policy_analysis?.applicable_policies?.length > 0 && (
                  <div className="mb-2">
                    <div className="flex flex-wrap gap-1">
                      {aiResult.policy_analysis.applicable_policies.map((pol: string, idx: number) => (
                        <span key={idx} className="text-[10px] font-semibold bg-teal-50 text-teal-800 border border-teal-200 rounded px-1.5 py-0.5 truncate max-w-full">
                          {pol}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <p className="text-xs text-slate-600 leading-relaxed mb-3">
                  {aiResult.policy_analysis?.implications}
                </p>
              </div>

              {aiResult.historical_analysis?.comparison_summary && (
                <div className="pt-2 border-t border-slate-100">
                  <span className="text-[10px] font-bold uppercase text-slate-400 block mb-1">Precedent Comparison</span>
                  <p className="text-[11px] text-slate-700 bg-slate-50 border border-slate-200 rounded px-2 py-1 leading-snug">
                    {aiResult.historical_analysis.comparison_summary}
                  </p>
                </div>
              )}
            </div>

          </div>

        </div>
      )}

      {/* 3. Deterministic Explanation & Evidence Comparison */}
      <div className="space-y-4">
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-900 mb-2 flex items-center">
            <FileSearch className="w-4 h-4 mr-2 text-slate-500" />
            Deterministic Ground Truth
          </h3>
          <p className="text-sm text-slate-600 leading-relaxed">
            {explanation}
          </p>
          {detail.evidence.matched_by && detail.evidence.matched_by.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-200">
              <span className="text-xs text-slate-500 font-medium">Deterministic rules matched:</span>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {detail.evidence.matched_by.map((rule, idx) => (
                  <span key={idx} className="bg-white border border-slate-200 text-slate-700 text-xs px-2.5 py-0.5 rounded-md font-mono">
                    {rule}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Deep Evidence Comparison (3-way table) */}
        <div>
          <h3 className="text-sm font-semibold text-slate-900 mb-2">Evidence Comparison</h3>
          <EvidenceComparison evidence={detail.evidence} />
        </div>
      </div>
    </div>
  );
}
