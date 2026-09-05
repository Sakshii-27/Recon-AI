"""Domain models for Recon-AI.

Defines Pydantic models for ERP Orders, Gateway Transactions,
Gateway Settlements, Bank Transactions, and isolated Ground Truth cases.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ERPOrder(BaseModel):
    """Represents an order recorded in the Merchant's ERP or Billing system."""
    order_id: str = Field(..., description="Unique internal order identifier, e.g. ORD-10042")
    order_reference: str = Field(..., description="Customer-facing or checkout reference, e.g. WEB-8F92K")
    order_date: str = Field(..., description="Order creation date in YYYY-MM-DD format")
    customer_id: str = Field(..., description="Customer identifier, e.g. CUS-1042")
    gross_amount: float = Field(..., description="Gross order amount in currency units")
    currency: str = Field("INR", description="Currency code, e.g. INR")
    payment_method: str = Field(..., description="Payment method used, e.g. UPI, Card, NetBanking, Wallet")
    order_status: str = Field("PAID", description="Order status, e.g. PAID, PENDING, CANCELLED")


class GatewayTransaction(BaseModel):
    """Represents a transaction captured by the Payment Gateway (e.g. Razorpay/Stripe)."""
    gateway_transaction_id: str = Field(..., description="Gateway transaction ID, e.g. TXN-50042")
    order_reference: str = Field(..., description="Order reference passed during payment checkout")
    captured_amount: float = Field(..., description="Amount successfully captured by the gateway")
    transaction_date: str = Field(..., description="Capture date in YYYY-MM-DD format")
    payment_status: str = Field("CAPTURED", description="Status: CAPTURED, REFUNDED, DISPUTED, FAILED")
    payment_method: str = Field(..., description="Method: UPI, Card, NetBanking, Wallet")
    gateway_fee: float = Field(..., description="Merchant Discount Rate (MDR) fee deducted")
    gst_on_fee: float = Field(..., description="GST on the gateway fee")
    refund_amount: float = Field(0.0, description="Amount refunded to the customer")
    chargeback_amount: float = Field(0.0, description="Amount deducted due to chargeback dispute")
    settlement_id: Optional[str] = Field(None, description="Batch settlement ID if included in a settlement batch")
    settlement_date: Optional[str] = Field(None, description="Date the settlement batch was scheduled/processed")


class GatewaySettlement(BaseModel):
    """Represents a bundled payout/settlement record issued by the Payment Gateway."""
    settlement_id: str = Field(..., description="Settlement batch ID, e.g. SET-20260831-001")
    settlement_date: str = Field(..., description="Date of settlement payout in YYYY-MM-DD format")
    gross_amount: float = Field(..., description="Sum of captured amounts for transactions in this batch")
    total_mdr: float = Field(..., description="Total MDR deducted across all transactions")
    total_gst: float = Field(..., description="Total GST on MDR deducted")
    refunds: float = Field(0.0, description="Total refunds deducted in this batch")
    chargebacks: float = Field(0.0, description="Total chargebacks deducted in this batch")
    net_settlement: float = Field(..., description="Net payout amount sent to merchant bank account")
    transaction_ids: List[str] = Field(default_factory=list, description="List of gateway transaction IDs in this batch")


class BankTransaction(BaseModel):
    """Represents an entry on the merchant's corporate bank statement."""
    bank_transaction_id: str = Field(..., description="Bank statement line identifier, e.g. BANK-80042")
    transaction_date: str = Field(..., description="Posting date on the bank statement in YYYY-MM-DD format")
    description: str = Field(..., description="Statement narrative/narration text from the bank feed")
    reference: str = Field(..., description="Reference string or UTR number from bank statement")
    credit_amount: float = Field(0.0, description="Credit amount deposited into merchant account")
    debit_amount: float = Field(0.0, description="Debit amount withdrawn from merchant account")
    balance: float = Field(..., description="Sequential running account balance after this transaction")
    bank_utr: Optional[str] = Field(None, description="Unique Transaction Reference (NEFT/RTGS/IMPS/UPI)")


class GroundTruthCase(BaseModel):
    """Isolated ground-truth mapping for evaluation and benchmarking only.
    
    This model is NEVER read by the reconciliation engine during operational runs.
    """
    case_id: str = Field(..., description="Unique evaluation case identifier, e.g. CASE-0042")
    scenario: str = Field(..., description="Target scenario class, e.g. EXACT_MATCH, BATCH_SETTLEMENT, etc.")
    erp_order_ids: List[str] = Field(default_factory=list, description="IDs of linked ERP orders")
    gateway_transaction_ids: List[str] = Field(default_factory=list, description="IDs of linked Gateway transactions")
    settlement_id: Optional[str] = Field(None, description="Linked settlement batch ID, if applicable")
    bank_transaction_ids: List[str] = Field(default_factory=list, description="IDs of linked Bank transactions")
    expected_relationship: str = Field(..., description="1_TO_1, N_TO_1, 1_TO_0, 0_TO_1, 1_TO_N, UNKNOWN")
    expected_net_amount: float = Field(..., description="Calculated expected net monetary settlement")
    actual_bank_amount: Optional[float] = Field(None, description="Actual amount credited in bank, if any")
    root_cause: Optional[str] = Field(None, description="Expected root cause if this case is an exception")
    is_exception: bool = Field(..., description="Whether this case should result in an exception")
    description: str = Field(..., description="Human-readable description of this case and edge condition")
