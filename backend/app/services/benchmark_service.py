"""Benchmark Service Layer.

Scans the data/benchmark directory to serve historical Phase 3 baseline results.
"""
import json
from pathlib import Path
from typing import Dict, Any

from backend.app.api.schemas.benchmark import BenchmarkBaselineResponse

BENCHMARK_DIR = Path("data/benchmark")


class BenchmarkService:
    """Service layer for serving benchmark results."""
    
    def get_baseline_results(self) -> BenchmarkBaselineResponse:
        """Reads JSON reports from data/benchmark and returns the baseline metrics."""
        baseline: Dict[str, Dict[str, Any]] = {}
        
        if BENCHMARK_DIR.exists():
            for report_file in BENCHMARK_DIR.glob("benchmark_*.json"):
                try:
                    with open(report_file, "r") as f:
                        data = json.load(f)
                    
                    dataset_size = data.get("benchmark_metadata", {}).get("dataset_size", "unknown")
                    if str(dataset_size) not in ["100", "500", "1000"]:
                        continue
                        
                    acc = data.get("accuracy", {})
                    fin = data.get("financial", {})
                    auto = data.get("autonomous_resolution", {})
                    
                    # Compute simplified baseline stats as expected in prompt
                    # precision, recall, f1, match_rate, value_reconciled, safe_autonomous, false_negatives
                    baseline[str(dataset_size)] = {
                        "precision": acc.get("precision", 0.0) / 100.0,
                        "recall": acc.get("recall", 0.0) / 100.0,
                        "f1": acc.get("f1_score", 0.0) / 100.0,
                        "match_rate": acc.get("match_rate", 0.0) / 100.0,
                        "value_reconciled": fin.get("value_reconciliation_percentage", 0.0) / 100.0,
                        "safe_autonomous": auto.get("safe_autonomous_resolution_rate", 0.0) / 100.0,
                        "false_negatives": acc.get("false_negative_count", 0)
                    }
                except (json.JSONDecodeError, KeyError, Exception) as e:
                    # Ignore invalid files
                    print(f"Error reading {report_file}: {e}")
                    
        return BenchmarkBaselineResponse(baseline=baseline)


# Global singleton
benchmark_service = BenchmarkService()
