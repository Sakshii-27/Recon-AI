"""Configuration for the Recon-AI Deterministic Engine."""

from decimal import Decimal

# Confidence Thresholds
AUTO_RESOLVE_THRESHOLD = 0.95
REVIEW_THRESHOLD = 0.70

# Tolerances
AMOUNT_TOLERANCE = Decimal("0.01")  # 1 paisa precision for float mismatch
DATE_TOLERANCE_DAYS = 3             # Match dates up to T+3

# Re-use global constants from finance_rules
from backend.app.domain.finance_rules import DEFAULT_MDR_RATE, DEFAULT_GST_ON_MDR
MDR_RATE = DEFAULT_MDR_RATE
GST_RATE = DEFAULT_GST_ON_MDR
