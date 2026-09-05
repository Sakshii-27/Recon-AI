<div align="center">

# ReconPulse AI

**Autonomous Multi-Source Financial Reconciliation & AI-Powered Exception Investigation**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_AI-1C3C3C?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Gemini](https://img.shields.io/badge/Gemini_2.5-Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev)
[![Tests](https://img.shields.io/badge/Tests-67_Passed-brightgreen?logo=pytest&logoColor=white)](#-testing--benchmark)

*Match transactions across ERP, Gateway, and Bank in milliseconds - investigate exceptions with auditable AI reasoning.*

</div>

---

## The Problem

Every business that accepts digital payments must reconcile three disconnected systems:

| Source | What It Records | Example |
|--------|----------------|---------|
| **ERP** (SAP, Tally) | Customer placed an order | *"Order #1234 - ₹10,000"* |
| **Payment Gateway** (Razorpay) | Payment captured, fees deducted, amount settled | *"Captured ₹10,000 → Fees ₹236 → Settled ₹9,764"* |
| **Bank Statement** | Money deposited into the account | *"Credit: ₹9,764"* |

Today, finance teams manually cross-check these in Excel - row by row, file by file. This leads to:
- 💸 **Revenue leakage** - gateway fee overcharges go unnoticed
- 🔁 **Duplicate charges** - customer disputes pile up
- 🕳️ **Missing settlements** - ₹10L+ goes undetected for weeks
- 📉 **Unreliable cash forecasts** - partial settlements break projections

---

## The Solution

ReconPulse AI uses a **hybrid architecture** - a deterministic engine handles the predictable 90%, while AI investigates the complex 10%.

```
┌─────────────────────────────────────────────────────────────────┐
│                     1,000 Transactions                          │
├──────────────────────────────┬──────────────────────────────────┤
│    ~900 Auto-Resolved        │      ~100 Exceptions             │
│   by Deterministic Engine    │   investigated by AI Pipeline    │
│   (milliseconds, zero cost)  │   (LangGraph + RAG + Gemini)     │
└──────────────────────────────┴──────────────────────────────────┘
```

> **The Golden Rule:** The engine is deterministic, the AI is advisory. AI *never* auto-resolves financial decisions - `human_review_required` is always `True`.

---

## Key Features

| Feature | Description |
|---------|-------------|
| 📊 **Real-Time Dashboard** | KPI cards, match rate progress, cash position, and exception analytics |
| ⚙️ **3-Tier Reconciliation Engine** | 1:1 ID matching → Fee validation (MDR + GST) → N:1 batch settlement |
| 🤖 **AI Exception Investigation** | LangGraph pipeline: Evidence → Policy RAG → Historical Precedent → Risk Audit |
| 💬 **Finance Copilot** | Natural-language chatbot grounded in your actual reconciliation data |
| 📈 **Cash Flow Forecast** | Deterministic 7-day projection based on unsettled gateway captures |
| 🧪 **Benchmark Evaluator** | Ground-truth comparison with Precision, Recall, F1, and Value Coverage |
| 🛡️ **Safety-First AI** | Independent Risk Validator that can only *downgrade* decisions, never escalate |

---

## Architecture

### How Data Flows Through the System

```
User clicks "Run Reconciliation" (1,000 records, seed: 42)
                    │
                    ▼
    ┌───────────────────────────────┐
    │    Synthetic Data Generator   │
    │  ERP · Gateway · Bank · Truth │
    └───────────────┬───────────────┘
                    │
        ┌───────────▼───────────┐
        │   3-TIER ENGINE       │
        │                       │
        │  Tier 1 → ID Matching │  "Gateway ID found in bank narration → 100% match"
        │  Tier 2 → Fee Math    │  "Expected: ₹9,764 | Bank: ₹9,764 | Diff: ₹0.00 ✓"
        │  Tier 3 → Batch N:1   │  "5 gateway txns sum to 1 bank deposit"
        │  Tier 4 → Exceptions  │  "Flag stragglers: Missing Bank / Missing ERP / Duplicate"
        │                       │
        └──────┬────────┬───────┘
               │        │
       ┌───────▼──┐   ┌─▼─────────────────────────────┐
       │ RESOLVED │   │ EXCEPTIONS (REVIEW)           │
       │ ~90%     │   │ ~10%                          │
       │ Dashboard│   │                               │
       └──────────┘   │  ┌─────────────────────────┐  │
                      │  │ LangGraph AI Pipeline   │  │
                      │  │                         │  │
                      │  │ 1. Evidence Analyzer    │  │
                      │  │ 2. Policy RAG (ChromaDB)│  │
                      │  │ 3. Historical Precedent │  │
                      │  │ 4. Risk Validator       │  │
                      │  │    (can only downgrade) │  │
                      │  └─────────────────────────┘  │
                      └───────────────────────────────┘
```

### The 3 Layers Explained

**1. Frontend - The Control Room** (Next.js 16)
- **Dashboard:** Real-time KPIs - match rate, cash position, exception breakdown
- **Exception Workbench:** Click into any exception, see evidence side-by-side, trigger AI investigation
- **Finance Copilot:** Ask *"What's the total unreconciled value?"* - get grounded answers instantly

**2. Backend - The Brain** (FastAPI + Python)
- **Tier 1:** Exact ID matching. Gateway Transaction ID found in the bank narration? → 100% confidence match.
- **Tier 2:** Financial validation. Independently calculates `Gross − MDR − GST ± Refunds ± Chargebacks` and checks if it matches the bank deposit to within ₹0.01.
- **Tier 3:** Batch settlement. A gateway bundles 5 transactions into one bank deposit. This tier sums all 5 expected net amounts and matches the total against the single bank entry.
- **Exception Detector:** Anything left unmatched is classified as `MISSING_BANK`, `MISSING_ERP`, or `DUPLICATE`.

**3. AI Investigator - The Detective** (LangGraph + Gemini)
1. **Evidence Analyzer** - Parses structured financial evidence, flags anomalies
2. **Policy RAG** - Retrieves relevant company financial policies from ChromaDB
3. **Historical Comparator** - Finds similar past exceptions and how they were resolved
4. **Risk Validator** - Independent safety audit. Can only *downgrade* AI decisions to `HUMAN_REVIEW`. Never escalates.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 16, React, TailwindCSS, Recharts | Dashboard, Exception Workbench, Copilot |
| Backend | FastAPI, Python 3.12, Uvicorn | REST API, Reconciliation Engine |
| AI / LLM | Google Gemini 2.5 Flash | Exception investigation, Copilot responses |
| Agentic Framework | LangGraph, LangChain | Multi-stage AI reasoning pipeline |
| Vector Store (RAG) | ChromaDB, Gemini Embeddings | Policy & historical case retrieval |
| Data Layer | Pydantic Models (in-memory) | Synthetic financial data generation |
| Testing | Pytest (67 tests) | API, Engine, Benchmark, Financial Rules |

---

## Benchmark Results

The engine is evaluated against isolated ground truth data that it **never sees** during reconciliation:

| Metric | Score |
|--------|-------|
| **Precision** | 93.69% |
| **Recall** | 100.00% |
| **F1 Score** | 96.74% |
| **Match Rate** | 88.99% |
| **Value Reconciled** | 88.46% |
| **Safe Autonomous Precision** | 91.33% |

> Ground truth is generated alongside the synthetic data but is strictly isolated - the engine has zero access to it. This ensures benchmark metrics are honest and unbiased.

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API Key *(optional - system runs in mock mode without it)*

### 1. Clone & Setup Backend

```bash
git clone https://github.com/Sakshii-27/Recon-AI.git
cd Recon-AI

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn pydantic langchain langgraph langchain-google-genai chromadb python-dotenv pytest httpx

# Configure environment (optional - for real AI features)
echo "AI_PROVIDER=gemini" > .env
echo "AI_API_KEY=your_gemini_api_key_here" >> .env
echo "AI_MODEL=gemini-2.5-flash" >> .env

# Start the API server
uvicorn backend.app.main:app --reload
# → http://127.0.0.1:8000/docs (Swagger UI)
```

### 2. Setup Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000 (Dashboard)
```

### 3. Run a Reconciliation
Open `http://localhost:3000`, enter the number of records (e.g. `1000`), and click **Run Reconciliation**. The dashboard will populate with real-time metrics, exceptions, and cash position data.

---

## Testing & Benchmark

```bash
# Run the full test suite (67 tests)
pytest tests/

# Run the benchmark evaluator against ground truth
python scripts/run_final_benchmark.py
```

---

## Project Structure

```
Recon-AI/
├── backend/
│   └── app/
│       ├── main.py                        # FastAPI entrypoint
│       ├── api/routes/                    # REST endpoints
│       ├── reconciliation/                # 3-Tier Deterministic Engine
│       │   ├── engine.py                  #   Orchestrator
│       │   ├── tier1_matcher.py           #   ID-based matching
│       │   ├── tier2_financial.py         #   Fee validation
│       │   ├── tier3_batch.py             #   N:1 batch settlement
│       │   └── exceptions_detector.py     #   Straggler detection
│       ├── ai/                            # AI Investigation Layer
│       │   ├── resolver.py                #   LLM + Embedding providers
│       │   ├── investigation/graph.py     #   LangGraph 4-node pipeline
│       │   └── rag/vector_store.py        #   ChromaDB RAG
│       ├── copilot/                       # Finance Copilot
│       ├── benchmark/                     # Evaluation system
│       ├── data_generation/               # Synthetic data (13 scenarios)
│       ├── domain/                        # Pydantic models + finance rules
│       └── finance/                       # Cash position + forecast
├── frontend/
│   └── src/
│       ├── app/page.tsx                   # Main dashboard
│       ├── components/
│       │   ├── dashboard/                 # KPIs, charts, health panels
│       │   ├── exceptions/                # Exception workbench
│       │   └── copilot/                   # Chat widget
│       └── services/api.ts               # API client
├── tests/                                 # 67 pytest tests
└── scripts/                               # Benchmark & utility scripts
```

---

##  Key Design Decisions

| Decision | Why |
|----------|-----|
| **Deterministic first, AI second** | The engine resolves ~90% with zero AI cost. AI only handles the hard cases. |
| **Ground truth is strictly isolated** | The engine never sees ground truth. Benchmark metrics are honest. |
| **AI never auto-resolves** | `human_review_required = True` always. Prevents hallucination-driven financial losses. |
| **Risk Validator can only downgrade** | The safety node can reject AI proposals, never escalate them. |
| **Graceful fallback** | Missing API key or AI timeout? System returns `INSUFFICIENT_EVIDENCE` - never fabricates mock data in production. |
| **LangGraph over simple prompting** | Breaking reasoning into Evidence → Policy → History → Risk makes each step auditable. |

---

##  License

This project is licensed under the MIT License.
