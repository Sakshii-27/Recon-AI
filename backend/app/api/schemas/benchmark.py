"""Benchmark API Schemas."""
from typing import Any, Dict
from pydantic import BaseModel, Field


class BenchmarkBaselineResponse(BaseModel):
    """Phase 3 deterministic benchmark baselines response."""
    baseline: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Benchmark metrics keyed by dataset size (e.g. '100', '500', '1000')"
    )
