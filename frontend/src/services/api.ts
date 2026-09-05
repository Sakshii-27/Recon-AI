export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

// --- Types ---

export interface ReconciliationRunRequest {
  records: number;
  seed: number;
}

export interface ReconciliationSummary {
  total_records: number;
  matched: number;
  exceptions: number;
  match_rate: number;
  value_reconciled: number;
  safe_autonomous_rate: number;
}

export interface ReconciliationResponse {
  summary: ReconciliationSummary;
  matches: any[];
  exceptions: any[];
  decisions: any[];
  financial_summary: FinancialSummaryResponse;
  metadata: any;
}

export interface ExceptionEvidence {
  matched_by: string[];
  erp_evidence: any[];
  gateway_evidence: any[];
  bank_evidence: any[];
  financial_evidence: any | null;
}

export interface ExceptionDetail {
  id: string;
  type: string;
  status: string;
  amount: number;
  difference: number;
  confidence: number;
  evidence: ExceptionEvidence;
  related_records: Record<string, string[]>;
}

export interface ExceptionListResponse {
  total_exceptions: number;
  exceptions: ExceptionDetail[];
}

export interface BenchmarkBaselineResponse {
  baseline: Record<
    string,
    {
      precision: number;
      recall: number;
      f1: number;
      match_rate: number;
      value_reconciled: number;
      safe_autonomous: number;
      false_negatives: number;
    }
  >;
}

export interface FinancialSummaryResponse {
  gross_sales: number;
  gateway_captured: number;
  gateway_fees: number;
  gateway_gst: number;
  expected_settlement: number;
  bank_settlement: number;
  unreconciled_value: number;
}

// --- API Methods ---

export async function fetchHealth(): Promise<{ status: string }> {
  const url = `${API_BASE_URL.replace("/api/v1", "")}/health`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch health");
  return res.json();
}

export async function runReconciliation(
  request: ReconciliationRunRequest
): Promise<ReconciliationResponse> {
  const res = await fetch(`${API_BASE_URL}/reconciliation/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to run reconciliation");
  }
  return res.json();
}

export async function fetchBenchmark(): Promise<BenchmarkBaselineResponse> {
  const res = await fetch(`${API_BASE_URL}/benchmark`);
  if (!res.ok) throw new Error("Failed to fetch benchmark data");
  return res.json();
}

export async function fetchSummary(): Promise<ReconciliationSummary> {
  const res = await fetch(`${API_BASE_URL}/reconciliation/summary`);
  if (!res.ok) throw new Error("Failed to fetch reconciliation summary");
  return res.json();
}

export async function fetchExceptions(type?: string): Promise<ExceptionListResponse> {
  const url = type ? `${API_BASE_URL}/exceptions?type=${type}` : `${API_BASE_URL}/exceptions`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch exceptions");
  return res.json();
}

export async function fetchException(id: string): Promise<ExceptionDetail> {
  const res = await fetch(`${API_BASE_URL}/exceptions/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch exception ${id}`);
  return res.json();
}

export async function resolveWithAI(exception_id: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/ai/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ exception_id }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to resolve with AI");
  }
  return res.json();
}

export async function investigateWithAIV2(exception_id: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/ai/investigate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ exception_id }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to investigate with AI V2");
  }
  return res.json();
}

export async function fetchFinancialSummary(): Promise<FinancialSummaryResponse> {
  const res = await fetch(`${API_BASE_URL}/financial-summary`);
  if (!res.ok) throw new Error("Failed to fetch financial summary");
  return res.json();
}

export async function fetchCashPosition(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/cash-position`);
  if (!res.ok) throw new Error("Failed to fetch cash position");
  return res.json();
}

export async function fetchCashForecast(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/cash-forecast`);
  if (!res.ok) throw new Error("Failed to fetch cash forecast");
  return res.json();
}

export interface CopilotQueryResponse {
  answer: string;
  supporting_data: Record<string, any>;
  source_sections: string[];
  confidence: string;
  requires_human_review: boolean;
}

export async function queryCopilot(question: string, exception_id?: string): Promise<CopilotQueryResponse> {
  const res = await fetch(`${API_BASE_URL}/copilot/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, exception_id })
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.detail || "Failed to fetch response from Copilot");
  }
  return res.json();
}
