# Chargeback & Dispute Handling Policy

## Purpose
Defines the accounting treatment for customer payment disputes, chargeback debits, and representment reversals.

## Core Rules
1. **Immediate Bank Debit**: When an acquiring bank or card network receives a chargeback, the disputed amount plus the chargeback handling fee is immediately debited from the merchant's settlement account.
2. **Reconciliation Status**:
   - A disputed transaction must be linked to its original capture.
   - Net expected settlement for a chargebacked transaction is `0.00` or negative (if chargeback fee applies).
3. **Representment**:
   - If the merchant wins the representment dispute, the funds are credited back in a subsequent settlement batch.
   - The credit must be matched against the open chargeback receivable account.
