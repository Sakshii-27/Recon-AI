"""Scenario definitions and scenario distribution planner for Recon-AI.

Controls the exact composition of edge cases, clean matches, batch settlements,
and unresolvable anomalies in the synthetic dataset.
"""

from enum import Enum
from typing import Dict


class ScenarioType(str, Enum):
    """The 13 distinct financial reconciliation scenario classes."""
    EXACT_MATCH = "EXACT_MATCH"
    MDR_GST = "MDR_GST"
    T_PLUS_1 = "T_PLUS_1"
    T_PLUS_2 = "T_PLUS_2"
    BATCH_SETTLEMENT = "BATCH_SETTLEMENT"
    REFUND = "REFUND"
    CHARGEBACK = "CHARGEBACK"
    PARTIAL_SETTLEMENT = "PARTIAL_SETTLEMENT"
    DUPLICATE = "DUPLICATE"
    MISSING_BANK = "MISSING_BANK"
    MISSING_ERP = "MISSING_ERP"
    FEE_ANOMALY = "FEE_ANOMALY"
    AMBIGUOUS = "AMBIGUOUS"


# Base scenario weights that sum to 100%
SCENARIO_PERCENTAGES: Dict[ScenarioType, float] = {
    ScenarioType.EXACT_MATCH: 30.0,
    ScenarioType.MDR_GST: 15.0,
    ScenarioType.T_PLUS_1: 10.0,
    ScenarioType.T_PLUS_2: 8.0,
    ScenarioType.BATCH_SETTLEMENT: 10.0,
    ScenarioType.REFUND: 5.0,
    ScenarioType.CHARGEBACK: 5.0,
    ScenarioType.PARTIAL_SETTLEMENT: 5.0,
    ScenarioType.DUPLICATE: 4.0,
    ScenarioType.MISSING_BANK: 3.0,
    ScenarioType.MISSING_ERP: 2.0,
    ScenarioType.FEE_ANOMALY: 2.0,
    ScenarioType.AMBIGUOUS: 1.0,
}


def plan_scenario_distribution(total_cases: int = 100) -> Dict[ScenarioType, int]:
    """Calculates the exact integer scenario quotas for a requested dataset volume.

    Ensures that every scenario type receives at least 1 case, and the sum
    equals total_cases exactly.
    """
    if total_cases < len(ScenarioType):
        raise ValueError(f"total_cases must be at least {len(ScenarioType)}")

    distribution: Dict[ScenarioType, int] = {}
    allocated = 0

    for scenario, pct in SCENARIO_PERCENTAGES.items():
        count = max(1, int(round((pct / 100.0) * total_cases)))
        distribution[scenario] = count
        allocated += count

    # Adjust rounding differences on EXACT_MATCH
    diff = total_cases - allocated
    distribution[ScenarioType.EXACT_MATCH] += diff

    return distribution
