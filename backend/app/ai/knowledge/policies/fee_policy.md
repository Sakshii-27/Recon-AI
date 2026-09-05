# Fee Policy & MDR Validation SOP

## Purpose
Establishes the rules for verifying payment gateway transaction fees (Merchant Discount Rate - MDR) and applicable GST.

## Standard Fee Structure
- **Standard Net Banking / Debit Card MDR**: 1.50% of gross transaction value
- **Standard Credit Card MDR**: 2.00% of gross transaction value
- **GST on Processing Fees**: 18.00% applied strictly to the gateway fee amount

## Fee Calculation Formula
```
Gateway Fee = Gross Transaction Value * Contracted MDR Rate
GST Amount = Gateway Fee * 0.18
Total Fee Deduction = Gateway Fee + GST Amount
Expected Net Settlement = Gross Transaction Value - Total Fee Deduction
```

## Discrepancy Tolerance
- Discrepancies <= INR 1.00 are treated as normal rounding differences.
- Discrepancies > INR 1.00 must be flagged as `FEE_ANOMALY` for contract renegotiation or debit note issuance.
