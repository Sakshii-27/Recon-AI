[SYNTHETIC — Demo Policy Document]

# Duplicate Transaction Policy

## Definition
A duplicate transaction occurs when the same order is captured multiple times by the payment gateway, or when a payment gateway retry mechanism results in multiple unique captures for the identical `order_reference`.

## Recognition
- Multiple Gateway transactions exist with the EXACT same `order_reference`.
- The ERP has only ONE order for that `order_reference`.
- The timestamps are usually very close, often within seconds or minutes.
- The amount may be identical, but occasionally varies if retry fees were applied.

## Policy Implications
If an AI investigator identifies multiple captured gateway transactions sharing the same order reference, and only one is required to satisfy the ERP order amount, the excess transaction(s) MUST be flagged as LIKELY_DUPLICATE.

## Required Evidence
- Gateway transaction footprints must share the same `order_reference`.
- The sum of captured amounts must be greater than the ERP expected amount.
- There must be no separate distinct ERP order matching the excess gateway transactions.

## Resolution
If flagged as a duplicate, manual review is required to initiate a refund to the customer for the excess capture. Do NOT mark the transaction as fully resolved automatically.
