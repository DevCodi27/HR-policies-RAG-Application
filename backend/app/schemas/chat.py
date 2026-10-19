from typing import Optional, Any, Literal
from pydantic import BaseModel, Field

class ChatQueryRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="Employee question or prompt"
    )
    employee_id: Optional[str] = Field(
        default=None,
        description="Optional employee ID for authenticated/scopd queries"
    )
    agent_mode: Literal["single", "multi"] = Field(                                                                                   
        default="single",                                                                                                             
        description="Agent execution strategy: 'single' (fast ReAct loop) or 'multi' (specialized multi-agent team)"                  
    )


class ChatQueryResponse(BaseModel):
    reply: str
    model: str
    latency_sec: float
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    tool_calls_executed: list[dict[str, Any]] = Field(default_factory=list)
    agent_mode: str = "single"