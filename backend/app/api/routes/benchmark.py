"""Benchmark Route."""
from fastapi import APIRouter

from backend.app.api.schemas.benchmark import BenchmarkBaselineResponse
from backend.app.services.benchmark_service import benchmark_service

router = APIRouter()

@router.get("", response_model=BenchmarkBaselineResponse)
def get_benchmarks():
    """Retrieves deterministic baseline results from Phase 3."""
    return benchmark_service.get_baseline_results()
