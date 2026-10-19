"""
Practice Exercise - Lesson 2: Token Budget Guardrail
File: policy-answer-desk/backend/practice_lesson2.py

How to run:
    Open PowerShell in: C:\\Users\\StanA\\OneDrive\\Desktop\\Projects\\policy-answer-desk
    Run: python backend/practice_lesson2.py
"""

import sys
import os

# Add backend directory to path so we can import our service
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.services.token_cost_calculator import count_tokens, compute_query_cost


def check_query_budget(
    prompt_text: str,
    max_budget_usd: float,
    estimated_completion_tokens: int = 300,
    model_name: str = "qwen-2.5-32b",
) -> tuple[bool, float]:
    """
    Checks if a query will stay within a specified USD budget.
    TODO: Implement this function:
    1. If max_budget_usd <= 0, raise a ValueError with message 'Budget must be greater than zero'.
    2. Count the prompt tokens using count_tokens(prompt_text).
    3. Compute total cost using compute_query_cost(prompt_tokens, estimated_completion_tokens, model_name).
    4. Extract 'total_cost' from the returned dictionary.
    5. Return a tuple: (total_cost <= max_budget_usd, total_cost).
    """
    # === YOUR CODE GOES HERE ===

    if max_budget_usd <= 0:
        raise ValueError("Budget must be greater than zero")
    prompt_tokens = count_tokens(prompt_text)
    cost_code = compute_query_cost(prompt_tokens, estimated_completion_tokens, model_name)
    total_cost  = cost_code["total_cost"]
    is_within_budget = total_cost<=max_budget_usd

    
    return(is_within_budget,max_budget_usd)
   
  


if __name__ == "__main__":
    print("Testing your check_query_budget implementation...")

    sample_prompt = "What is the notice period for Grade 3 in India under 2025 policy?"

    # Test 1: Valid query with generous budget ($0.01)
    is_ok, cost = check_query_budget(sample_prompt, max_budget_usd=0.01, model_name="qwen-2.5-32b")
    print(f"Test 1 - Generous Budget: within_budget={is_ok}, estimated_cost=${cost:.6f}")
    assert is_ok is True, "Test 1 Failed: Expected query to be within $0.01 budget"

    # Test 2: Tiny budget ($0.000001) that should fail
    is_ok, cost = check_query_budget(sample_prompt, max_budget_usd=0.000001, model_name="qwen-2.5-32b")
    print(f"Test 2 - Tiny Budget:     within_budget={is_ok}, estimated_cost=${cost:.6f}")
    assert is_ok is False, "Test 2 Failed: Expected query to exceed $0.000001 budget"

    # Test 3: Invalid budget <= 0 should raise ValueError
    try:
        check_query_budget(sample_prompt, max_budget_usd=0.0)
        assert False, "Test 3 Failed: Expected ValueError for non-positive budget"
    except ValueError as e:
        print(f"Test 3 - Error Check:     Successfully caught expected error: '{e}'")

    print("\nSUCCESS! All tests passed successfully!")
