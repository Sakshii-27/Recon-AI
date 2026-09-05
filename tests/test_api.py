"""API Tests for ReconPulse AI Phase 4."""
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

def test_health_check():
    """Test the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ReconPulse AI API"}

def test_reconciliation_run():
    """Test the /api/v1/reconciliation/run endpoint."""
    # Run a tiny reconciliation batch (20 records)
    payload = {"records": 20, "seed": 42}
    response = client.post("/api/v1/reconciliation/run", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected structure
    assert "summary" in data
    assert "matches" in data
    assert "exceptions" in data
    assert "decisions" in data
    assert "financial_summary" in data
    
    # Verify summary structure
    summary = data["summary"]
    assert summary["total_records"] == 20
    assert "matched" in summary
    assert "exceptions" in summary
    assert "match_rate" in summary
    assert "value_reconciled" in summary
    assert "safe_autonomous_rate" in summary

def test_benchmark_endpoint():
    """Test the /api/v1/benchmark endpoint."""
    response = client.get("/api/v1/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert "baseline" in data
    
    # Depending on whether benchmarks were generated in data/benchmark, 
    # it might have keys like '100', '500', '1000'
    # We just ensure the endpoint doesn't crash and returns the correct schema.
    assert isinstance(data["baseline"], dict)

def test_exceptions_endpoints():
    """Test the /api/v1/exceptions endpoints."""
    # Ensure there's a recent run to query against
    client.post("/api/v1/reconciliation/run", json={"records": 20, "seed": 42})
    
    # 1. Test listing all exceptions
    response = client.get("/api/v1/exceptions")
    assert response.status_code == 200
    data = response.json()
    assert "total_exceptions" in data
    assert "exceptions" in data
    assert isinstance(data["exceptions"], list)
    
    if data["total_exceptions"] > 0:
        first_exception = data["exceptions"][0]
        exc_id = first_exception["id"]
        
        # 2. Test filtering by type (root cause)
        exc_type = first_exception["type"]
        filter_response = client.get(f"/api/v1/exceptions?type={exc_type}")
        assert filter_response.status_code == 200
        filtered_data = filter_response.json()
        assert len(filtered_data["exceptions"]) > 0
        assert all(e["type"] == exc_type for e in filtered_data["exceptions"])
        
        # 3. Test getting a single exception by ID
        detail_response = client.get(f"/api/v1/exceptions/{exc_id}")
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert detail_data["id"] == exc_id
        assert "evidence" in detail_data
        assert "related_records" in detail_data

def test_exception_not_found():
    """Test 404 for an invalid exception ID."""
    response = client.get("/api/v1/exceptions/INVALID-ID-999")
    assert response.status_code == 404

def test_financial_summary_endpoint():
    """Test the /api/v1/financial-summary endpoint."""
    # Ensure there's a recent run
    client.post("/api/v1/reconciliation/run", json={"records": 20, "seed": 42})
    
    response = client.get("/api/v1/financial-summary")
    assert response.status_code == 200
    data = response.json()
    assert "gross_sales" in data
    assert "gateway_captured" in data
    assert "gateway_fees" in data
    assert "gateway_gst" in data
    assert "expected_settlement" in data
    assert "bank_settlement" in data
    assert "unreconciled_value" in data


def test_ai_resolve_endpoint():
    """Test the existing POST /api/v1/ai/resolve endpoint."""
    client.post("/api/v1/reconciliation/run", json={"records": 100, "seed": 42})
    exc_resp = client.get("/api/v1/exceptions")
    assert exc_resp.status_code == 200
    exceptions = exc_resp.json()["exceptions"]
    assert len(exceptions) > 0

    first_exc_id = exceptions[0]["id"]
    response = client.post("/api/v1/ai/resolve", json={"exception_id": first_exc_id})
    assert response.status_code == 200
    data = response.json()
    assert "decision" in data
    assert "confidence" in data
    assert "reasoning" in data
    assert data["human_review_required"] is True


def test_ai_investigate_endpoint():
    """Test the POST /api/v1/ai/investigate LangGraph + RAG endpoint."""
    client.post("/api/v1/reconciliation/run", json={"records": 100, "seed": 42})
    exc_resp = client.get("/api/v1/exceptions")
    exceptions = exc_resp.json()["exceptions"]
    
    first_exc_id = exceptions[0]["id"]
    response = client.post("/api/v1/ai/investigate", json={"exception_id": first_exc_id})
    assert response.status_code == 200
    data = response.json()
    assert "decision" in data
    assert "evidence_analysis" in data
    assert "policy_analysis" in data
    assert "historical_analysis" in data
    assert "risk_validation" in data
    assert data["human_review_required"] is True


def test_ai_fallback_safety():
    """Verify that when AI is unconfigured or fails, fallback never fabricates decisions."""
    import os
    from backend.app.ai.resolver import investigate_exception_v2
    
    # Force real provider with missing key
    prev_prov = os.environ.get("AI_PROVIDER")
    prev_key = os.environ.get("AI_API_KEY")
    try:
        os.environ["AI_PROVIDER"] = "gemini"
        if "AI_API_KEY" in os.environ:
            del os.environ["AI_API_KEY"]
            
        payload = {
            "id": "FALLBACK-TEST-1",
            "type": "BATCH_SETTLEMENT",
            "amount": 1000.0,
            "difference": 0.0,
            "evidence": {}
        }
        res = investigate_exception_v2(payload)
        assert res.is_fallback is True
        assert res.decision == "INSUFFICIENT_EVIDENCE"
        assert res.confidence == 0.0
        assert res.reasoning == "AI unavailable — deterministic evidence only."
        assert res.human_review_required is True
        assert res.risk_validation.approved is False
    finally:
        if prev_prov:
            os.environ["AI_PROVIDER"] = prev_prov
        else:
            os.environ["AI_PROVIDER"] = "mock"
        if prev_key:
            os.environ["AI_API_KEY"] = prev_key

