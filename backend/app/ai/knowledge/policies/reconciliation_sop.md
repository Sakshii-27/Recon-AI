# Standard Operating Procedure (SOP): Autonomous Financial Reconciliation

## Scope
Defines the deterministic matching hierarchy and exception workflow across ERP, Gateway, and Bank statements.

## 3-Way Reconciliation Hierarchy
1. **Tier 1 (Exact 1:1 Match)**: Exact match on Order ID / Transaction ID with amount variance == 0.00. Resolved autonomously.
2. **Tier 2 (MDR / Fee Reconciled)**: Captured amount minus contractual MDR and GST equals bank credit. Resolved autonomously.
3. **Tier 3 (Batch Settlement N:1)**: Multiple gateway captures aggregated under a single settlement ID matching bank deposit. Resolved autonomously if aggregate math is exact.
4. **Tier 4 (Exceptions / AI Investigation)**:
   - Ambiguities, duplicate signals, missing legs.
   - Forwarded to Evidence Analyst -> Policy Analyst -> Historical Analyst -> Decision Analyst -> Risk Validator.
   - All AI resolutions remain advisory; human review is strictly mandatory.
