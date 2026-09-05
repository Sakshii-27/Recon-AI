[SYNTHETIC — Demo Policy Document]

# Missing ERP Policy

## Definition
A Missing ERP exception occurs when there is evidence of payment capture and bank settlement, but no corresponding order exists in our internal ERP/OMS systems.

## Recognition
- Gateway transaction shows CAPTURED status.
- Bank statement confirms funds were deposited.
- No matching `order_reference` can be found in the ERP system.

## Policy Implications
This usually indicates an order drop issue in the checkout flow (e.g. payment succeeded but webhook to ERP failed). It is a critical revenue leakage issue in reverse (we have money but haven't fulfilled the service).

## Resolution
- Classify as LIKELY_MISSING_ERP.
- Manual review is required.
- The operations team must manually create the order in the ERP to fulfill the customer's purchase. Do NOT resolve automatically without operations approval.
