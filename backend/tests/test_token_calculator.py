import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.token_cost_calculator import (
    count_tokens,
    compute_query_cost,
    check_query_budget,
    MODEL_PRICING,
)

def test_count_tokens_empty_string():
    assert count_tokens("") == 0

def test_count_tokens_real_clause():
    text = "Clause 4.12(a)"
    # As verified, BPE splits this into 7 tokens
    count = count_tokens(text)
    assert count == 7

def test_compute_query_cost_standard():
    # 1,000,000 prompt tokens and 1,000,000 completion tokens on gpt-4o-mini
    # Rates: $0.15 input, $0.60 output
    result = compute_query_cost(1_000_000, 1_000_000, model_name="gpt-4o-mini")
    assert round(result["prompt_cost"], 4) == 0.1500
    assert round(result["completion_cost"], 4) == 0.6000
    assert round(result["total_cost"], 4) == 0.7500

def test_compute_query_cost_unknown_model():
    try:
        compute_query_cost(100, 50, model_name="unknown-model-xyz")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown model" in str(e)

def test_check_query_budget_generous():
    is_ok, cost = check_query_budget("Short test query", max_budget_usd=1.0)
    assert is_ok is True
    assert cost > 0

def test_check_query_budget_exceeded():
    is_ok, cost = check_query_budget("Short test query", max_budget_usd=0.0000001)
    assert is_ok is False
    assert cost > 0.0000001

def test_check_query_budget_invalid():
    try:
        check_query_budget("Short test query", max_budget_usd=0.0)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Budget must be greater than zero" in str(e)


if __name__ == "__main__":
    test_count_tokens_empty_string()
    test_count_tokens_real_clause()
    test_compute_query_cost_standard()
    test_compute_query_cost_unknown_model()
    print("All tests passed successfully!")
