# Settlement Timing & Cut-off Policy

## Purpose
Specifies standard settlement schedules (T+1, T+2) and rules for banking holidays and cut-off windows.

## Rules
1. **Standard Settlement Cycle**: Domestic transactions settle on a T+1 business day cycle.
2. **Weekend / Bank Holiday Rollover**: Transactions captured on Friday, Saturday, or Sunday settle together on Monday (or next working day).
3. **Missing Bank Window**: A transaction is not declared `MISSING_BANK` until T+3 working days have elapsed without credit.
