# Partial Settlement Policy

## Purpose
Guidelines for handling split transactions, partial captures, and multi-tranche bank deposits.

## Core Rules
1. **Multi-Tranche Deposits**: When a single high-value gateway order is settled across multiple bank deposit tranches, each bank transaction must be linked to the master gateway settlement ID.
2. **Variance Evaluation**:
   - Outstanding remainder must remain classified under `PARTIAL_SETTLEMENT` until the final tranche settles or T+3 window expires.
   - Partial refunds issued before settlement reduce the expected net amount accordingly.
