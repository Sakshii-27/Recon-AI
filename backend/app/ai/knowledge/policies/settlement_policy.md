[SYNTHETIC — Demo Policy Document]

# Settlement Policy

## Definition
A settlement refers to the consolidated transfer of funds from the Payment Gateway to the Merchant's Bank Account. 

## Batch Settlements
Often, the gateway will combine multiple individual captured transactions into a single payout, referred to as a "Batch Settlement".

## Recognition of Batch Settlements
- The Bank Statement will show a single deposit (e.g. ₹50,000).
- The Payment Gateway will have multiple individual transactions (e.g. ₹20,000 and ₹30,000) that share the same `settlement_id`.
- The sum of the Net Expected Settlement for these individual transactions MUST exactly equal the bank deposit amount.

## Policy Implications
If multiple unmatched gateway transactions sum exactly to an unmatched bank deposit, and they occurred within a reasonable timeframe (typically T+1 or T+2 days), they should be classified as a VALID_BATCH_SETTLEMENT. 

## Required Evidence
- Multiple gateway transactions.
- A single bank transaction.
- The mathematical sum of (Gateway Capture - Gateway Fee - GST) for all transactions must exactly match the Bank Deposit amount.
