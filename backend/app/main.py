"""FastAPI Application Entrypoint for ReconPulse AI."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment configuration
_env_path = Path(__file__).resolve().parent.parent.parent / "backend" / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import health, reconciliation, benchmark, exceptions, finance, ai, copilot

# Initialize FastAPI application
app = FastAPI(
    title="ReconPulse AI API",
    description="Autonomous Multi-Source Finance Reconciliation Controller API",
    version="0.4.0",  # Phase 4
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for local development (React frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(health.router, tags=["Health"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(reconciliation.router, prefix="/api/v1/reconciliation", tags=["Reconciliation"])
app.include_router(benchmark.router, prefix="/api/v1/benchmark", tags=["Benchmark"])
app.include_router(exceptions.router, prefix="/api/v1/exceptions", tags=["Exceptions"])
app.include_router(finance.router, prefix="/api/v1", tags=["Finance"])
app.include_router(copilot.router, prefix="/api/v1/copilot", tags=["Copilot"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
