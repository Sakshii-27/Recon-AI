import { useState } from "react";
import { MessageSquare, Send, Loader2, Info, AlertTriangle, ShieldCheck, X, Bot, Sparkles } from "lucide-react";
import { queryCopilot, CopilotQueryResponse } from "@/services/api";
import ReactMarkdown from 'react-markdown';

export function FinanceCopilot({ hasRun }: { hasRun: boolean }) {
  const [isOpen, setIsOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const [response, setResponse] = useState<CopilotQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const suggestedQuestions = [
    "What's our current cash position?",
    "What cash inflow is expected over the next 7 days?",
    "How much cash is at risk?",
    "What are our biggest unresolved exceptions?"
  ];

  async function handleAsk(q: string) {
    if (!hasRun) {
      setError("Run a reconciliation first so I can analyze the current financial data.");
      return;
    }
    
    if (!q.trim()) return;
    
    setLoading(true);
    setError(null);
    setResponse(null);
    setSubmittedQuestion(q);
    setQuestion("");
    
    try {
      const res = await queryCopilot(q);
      setResponse(res);
    } catch (err: any) {
      setError(err.message || "Failed to query the Finance Copilot.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {!isOpen ? (
        <div className="relative group">
          {/* Pulse background effect */}
          <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full blur opacity-30 group-hover:opacity-60 transition duration-1000 group-hover:duration-200 animate-pulse"></div>
          <button 
            onClick={() => setIsOpen(true)}
            className="relative flex items-center justify-center w-14 h-14 bg-gradient-to-tr from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white rounded-full shadow-xl transition-all duration-300 hover:scale-110 hover:shadow-indigo-500/40"
          >
            <Bot className="w-6 h-6" />
            <Sparkles className="w-3 h-3 absolute top-3 right-3 text-amber-300 animate-pulse" />
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl flex flex-col w-[380px] sm:w-[420px] max-h-[80vh] sm:max-h-[600px] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-slate-100 bg-slate-50">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-tr from-indigo-100 to-violet-100 text-indigo-700 rounded-lg shadow-sm border border-indigo-50">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900">Finance Copilot</h2>
                <p className="text-xs text-slate-500">Ask about the reconciliation run</p>
              </div>
            </div>
            <button 
              onClick={() => setIsOpen(false)} 
              className="text-slate-400 hover:text-slate-600 transition-colors p-1 rounded-md hover:bg-slate-200"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 p-4 overflow-y-auto bg-slate-50/50 flex flex-col">
            {!response && !loading && !error && (
              <div className="mb-4">
                <p className="text-xs text-slate-500 mb-3 font-medium">Suggested questions:</p>
                <div className="flex flex-col gap-2">
                  {suggestedQuestions.map((sq, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleAsk(sq)}
                      disabled={!hasRun}
                      className="text-left text-xs bg-white hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 px-3 py-2.5 rounded-lg transition-colors border border-slate-200 shadow-sm"
                    >
                      {sq}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {loading && (
              <div className="flex justify-center items-center py-10">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-50 text-red-800 rounded-lg flex items-center shadow-sm text-sm mb-4 border border-red-100">
                <AlertTriangle className="w-4 h-4 mr-2 flex-shrink-0" />
                <span className="font-medium">{error}</span>
              </div>
            )}

            {submittedQuestion && (
              <div className="flex justify-end mb-4">
                <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-[85%] shadow-sm">
                  <p className="text-sm">{submittedQuestion}</p>
                </div>
              </div>
            )}

            {response && (
              <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm relative mb-4">
                <div className="prose prose-sm prose-slate max-w-none">
                  <ReactMarkdown>{response.answer}</ReactMarkdown>
                </div>
                
                <div className="mt-4 pt-3 border-t border-slate-100 flex flex-col gap-3 text-xs">
                  {response.source_sections.length > 0 && (
                    <div className="flex items-center text-slate-500">
                      <span className="font-semibold mr-2">Source:</span>
                      {response.source_sections.join(", ")}
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center text-slate-500">
                      <span className="font-semibold mr-2">Confidence:</span>
                      <span className={`px-2 py-0.5 rounded ${
                        response.confidence === 'HIGH' ? 'bg-emerald-100 text-emerald-800' :
                        response.confidence === 'MEDIUM' ? 'bg-amber-100 text-amber-800' :
                        'bg-slate-200 text-slate-800'
                      }`}>
                        {response.confidence}
                      </span>
                    </div>

                    {response.requires_human_review && (
                      <div className="flex items-center text-amber-700 bg-amber-50 px-2 py-1 rounded border border-amber-200" title="Contains AI Recommendation">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        <span className="font-medium hidden sm:inline">AI Advice</span>
                      </div>
                    )}
                    
                    {!response.requires_human_review && response.confidence === 'HIGH' && (
                      <div className="flex items-center text-emerald-700 bg-emerald-50 px-2 py-1 rounded border border-emerald-200" title="Deterministic Facts Only">
                        <ShieldCheck className="w-3 h-3 mr-1" />
                        <span className="font-medium hidden sm:inline">Verified</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer Form */}
          <div className="p-4 bg-white border-t border-slate-100">
            <form 
              onSubmit={(e) => { e.preventDefault(); handleAsk(question); }}
              className="flex items-center space-x-2"
            >
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask something..."
                disabled={loading || !hasRun}
                className="flex-1 border border-slate-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-slate-50"
              />
              <button
                type="submit"
                disabled={loading || !question.trim() || !hasRun}
                className="bg-indigo-600 hover:bg-indigo-700 text-white p-2.5 rounded-lg transition-colors disabled:opacity-50 flex-shrink-0"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
