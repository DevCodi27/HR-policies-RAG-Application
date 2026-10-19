"""
Module: llm_client.py
Responsibility: Vendor-agnostic LLM client wrapper over Groq API.
Enforces:
- Automated token counting and latency tracking.
- Tool-calling compatibility.
- Environment-driven configuration.
"""

import os
import time
from typing import Optional, Any
from dotenv import load_dotenv
from groq import Groq

from app.services.token_cost_calculator import compute_query_cost

# Load environment configuration
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env")))

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "llama-3.3-70b-versatile")

# Initialize client
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def call_llm(
    messages: list[dict[str, str]],
    model_name: Optional[str] = None,
    tools: Optional[list[dict[str, Any]]] = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    """
    Executes a chat completion call with Groq and tracks execution metadata.

    Args:
        messages: Standard OpenAI/Groq message list [{"role": "...", "content": "..."}].
        model_name: Model identifier (defaults to DEFAULT_MODEL from .env).
        tools: Optional list of function tool schemas.
        temperature: Sampling temperature (default 0.0 for deterministic answers).
        max_tokens: Maximum tokens to generate.

    Returns:
        Dictionary containing:
          - 'content': Generated text content (str or None)
          - 'tool_calls': List of tool call objects if any
          - 'model': Model name used
          - 'latency_sec': Wall-clock latency in seconds
          - 'prompt_tokens': Number of prompt tokens
          - 'completion_tokens': Number of completion tokens
          - 'cost_usd': Total dollar cost calculated
    """
    if not client:
        raise ValueError("GROQ_API_KEY is not configured in .env.")

    target_model = model_name or DEFAULT_MODEL
    start_time = time.perf_counter()

    kwargs: dict[str, Any] = {
        "model": target_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = client.chat.completions.create(**kwargs)
    latency_sec = time.perf_counter() - start_time

    choice = response.choices[0]
    usage = response.usage

    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    cost_data = compute_query_cost(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        model_name=target_model,
    )

    return {
        "content": choice.message.content,
        "tool_calls": choice.message.tool_calls,
        "model": target_model,
        "latency_sec": round(latency_sec, 4),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost_data["total_cost"],
    }
