/**
 * TypeScript Data Contracts for Policy Answer Desk.
 * Directly mirrors FastAPI Pydantic schemas.
 */

export interface ToolExecutionRecord {
  tool_name: string;
  arguments: Record<string, any>;
  output: Record<string, any>;
}

export interface ChatQueryRequest {
  message: string;
  employee_id?: string | null;
  agent_mode?: 'single' | 'multi';
}

export interface ChatQueryResponse {
  reply: string;
  model: string;
  latency_sec: number;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  tool_calls_executed: ToolExecutionRecord[];
  agent_mode?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: Date;
  metadata?: {
    model?: string;
    latency_sec?: number;
    prompt_tokens?: number;
    completion_tokens?: number;
    cost_usd?: number;
    tool_calls_executed?: ToolExecutionRecord[];
    agent_mode?: string;
  };
}

export interface PolicyDocumentItem {
  id: number;
  title: string;
  filename: string;
  file_type: string;
  version: string;
  effective_date: string;
  entity: 'India' | 'UK' | 'Global';
  is_active: boolean;
  uploaded_at: string;
  total_chunks: number;
}

export interface DocumentListResponse {
  documents: PolicyDocumentItem[];
  total_count: number;
}

export interface TraceSpan {
  span_id: string;
  name: string;
  type: string;
  latency_sec: number;
  tokens?: number;
  cost_usd?: number;
  input?: any;
  output?: any;
  status?: string;
  model?: string;
}

export interface TraceRecord {
  trace_id: string;
  timestamp: string;
  employee_id: string;
  agent_mode: 'single' | 'multi';
  query: string;
  reply: string;
  model: string;
  latency_sec: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  status: string;
  tool_count: number;
  spans: TraceSpan[];
  langfuse_synced: boolean;
}

export interface TraceMetrics {
  total_traces: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_latency_sec: number;
  single_agent_traces: number;
  multi_agent_traces: number;
  langfuse_connected: boolean;
}

export interface TraceDashboardResponse {
  metrics: TraceMetrics;
  traces: TraceRecord[];
}
