"""
Module: token_cost_calculator.py
Responsibility: Calculate exact BPE token counts and compute API costs per request.
Dependencies: tiktoken
"""

import tiktoken

# Pricing table: Cost in USD per 1,000,000 tokens (Standard benchmark rates)
MODEL_PRICING: dict[str, dict[str, float]] = {
    # Groq Models
    "qwen/qwen3.8-27b": {
        "input_per_million": 0.20,
        "output_per_million": 0.20,
    },
    "qwen-2.5-32b": {
        "input_per_million": 0.20,
        "output_per_million": 0.20,
    },
    "llama-3.3-70b-versatile": {
        "input_per_million": 0.59,
        "output_per_million": 0.79,
    },
    "llama-3.1-8b-instant": {
        "input_per_million": 0.05,
        "output_per_million": 0.08,
    },
    # OpenAI & Anthropic Reference Rates
    "gpt-4o-mini": {
        "input_per_million": 0.15,
        "output_per_million": 0.60,
    },
    "gpt-4o": {
        "input_per_million": 2.50,
        "output_per_million": 10.00,
    },
    "claude-3-5-sonnet": {
        "input_per_million": 3.00,
        "output_per_million": 15.00,
    },
}

def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """
    Counts the exact number of BPE tokens in a given text string.
    
    Args:
        text: The string to tokenize.
        encoding_name: The tokenizer encoding (default: cl100k_base for modern LLMs).
        
    Returns:
        The total count of tokens as an integer.
    """
    if not text:
        return 0
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    return len(tokens)

def compute_query_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model_name: str = "gpt-4o-mini"
) -> dict[str, float]:
    """
    Calculates cost for prompt (input) and completion (output) tokens.
    
    Returns a dictionary with:
      - prompt_cost
      - completion_cost
      - total_cost
    """
    if model_name not in MODEL_PRICING:
        raise ValueError(
            f"Unknown model: '{model_name}'. Available models: {list(MODEL_PRICING.keys())}"
        )
    
    rates = MODEL_PRICING[model_name]
    prompt_cost = (prompt_tokens / 1_000_000.0) * rates["input_per_million"]
    completion_cost = (completion_tokens / 1_000_000.0) * rates["output_per_million"]
    total_cost = prompt_cost + completion_cost
    
    return {
        "prompt_cost": prompt_cost,
        "completion_cost": completion_cost,
        "total_cost": total_cost,
    }


def check_query_budget(
    prompt_text: str,
    max_budget_usd: float,
    estimated_completion_tokens: int = 300,
    model_name: str = "qwen-2.5-32b",
) -> tuple[bool, float]:
    """
    Checks if a query will stay within a specified USD budget limit.

    Args:
        prompt_text: The user's input prompt.
        max_budget_usd: Maximum allowable cost in USD.
        estimated_completion_tokens: Expected token count for the LLM response.
        model_name: Target model identifier.

    Returns:
        A tuple of (is_within_budget: bool, actual_estimated_cost: float).

    Raises:
        ValueError: If max_budget_usd is less than or equal to zero.
    """
    if max_budget_usd <= 0:
        raise ValueError("Budget must be greater than zero")

    prompt_tokens = count_tokens(prompt_text)
    cost_data = compute_query_cost(
        prompt_tokens=prompt_tokens,
        completion_tokens=estimated_completion_tokens,
        model_name=model_name,
    )
    actual_cost = cost_data["total_cost"]
    return (actual_cost <= max_budget_usd, actual_cost)

