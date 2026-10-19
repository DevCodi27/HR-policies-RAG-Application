# Full-Stack & GenAI Interview Preparation Guide

> **Focus**: Technologies, Libraries, Trade-offs & Senior-Level Interview Q&A  
> **Project**: HR Policy Answer Desk (Track C)  
> **Target Completion**: Tomorrow before 4:00 PM IST  
> **Last Updated**: 2026-10-18T19:05:00+05:30

---

## 1. Complete Technology Inventory

| Layer | Technology | Version | Purpose in Project | Alternative Considered | Why We Chose It |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Backend Runtime** | Python | 3.14 | Core backend logic & AI orchestration | Node.js / TypeScript | Python is the undisputed standard for AI/ML ecosystems, tokenizers, and LLM SDKs. |
| **Web Framework** | FastAPI | 0.115+ | High-performance async REST API | Flask / Django / Express | Built on ASGI / Starlette, automatic OpenAPI/Swagger docs, native Pydantic v2 validation. |
| **Data Validation** | Pydantic | 2.10+ | Contract validation & serialization | Marshmallow / Dataclasses | Rust-based `pydantic-core` is 5–15x faster; provides compile-time & runtime type safety. |
| **ORM** | SQLAlchemy | 2.0+ | Database modeling & transactions | Tortoise-ORM / Raw SQL | Mature connection pooling, ACID transaction guarantees, declarative models. |
| **Database Driver** | PyMySQL | 1.1+ | MySQL TCP client connection | `mysqlclient` / `asyncmy` | Pure Python driver with zero C-compiler dependencies; works reliably across all OSs. |
| **Database** | MySQL | 8.0 | System of record for policies & chunks | PostgreSQL / SQLite | Enterprise relational standard for audit trails, structured metadata, and cascading foreign keys. |
| **LLM Inference** | Groq LPU | Cloud API | Sub-second inference engine | OpenAI / Anthropic / Local Ollama | LPUs (Language Processing Units) achieve 500+ tokens/sec (~0.3s latency) at fraction of GPU cost. |
| **Model** | `qwen/qwen3.8-27b` | Latest | Reasoning & autonomous tool calling | `llama-3.3-70b` | Free tier, sub-second latency, robust multi-turn JSON tool schemas, zero hallucinations on employee records. |
| **Tokenizer** | `tiktoken` | 0.8+ | Exact token counting & cost estimation | HuggingFace `tokenizers` | OpenAI's blazing-fast Rust tokenizer; prevents OOMs and pre-flights inference costs. |
| **Frontend** | Angular | 19+ | Single Page Application (SPA) | React / Vue / Next.js | Enterprise-grade structure, strict TypeScript type checking, modern Signals reactive state. |
| **Test Runner** | `pytest` | 9.1+ | Automated unit & integration tests | `unittest` / Jest | Clean fixtures (`@pytest.fixture`), rich assertion introspection, sub-second test execution. |

---

## 2. In-Depth Technical Concepts & Architecture Trade-offs

### A. FastAPI & ASGI vs Node.js / Express
- **Mental Model**: In Express, routing and validation are decoupled (you use `express-validator` or `zod` manually). In FastAPI, route parameter annotations double as both **runtime validators** and **OpenAPI schema generators**.
- **ASGI (Asynchronous Server Gateway Interface)**: FastAPI runs on `uvicorn`, handling thousands of concurrent non-blocking HTTP requests using Python's `asyncio` event loop.

### B. SQLAlchemy 2.0 Architecture
1. **Engine (`create_engine`)**: Maintains a TCP connection pool. Avoids opening new sockets per request (which costs 20–50ms).
2. **`SessionLocal` (Unit of Work)**: Encapsulates database transactions. Every FastAPI request receives an isolated session via `Depends(get_db)`, auto-committed on success and rolled back on error.
3. **`Base = declarative_base()`**: The metaclass blueprint registry. Inspects all subclasses (`PolicyDocument`, `PolicyChunk`) and executes `CREATE TABLE IF NOT EXISTS` via `Base.metadata.create_all(bind=engine)`.
4. **Cascading Foreign Keys**: `chunks = relationship("PolicyChunk", back_populates="document", cascade="all, delete-orphan")` guarantees no orphaned chunks remain in MySQL when a policy document is deleted.

### C. Agentic Tool Calling (Function Calling Loop)
- **Why NOT LangChain or LlamaIndex?**
  *Interview Answer*: "LangChain introduces bloated abstractions, hidden prompts, and latency overhead. In enterprise AI, you need deterministic control over the exact system prompt, exact token budgets, and granular tool execution errors. Building the function-calling loop by hand in [`chat_service.py`](file:///C:/Users/StanA/OneDrive/Desktop/Projects/policy-answer-desk/backend/app/services/chat_service.py) gives us sub-second latency, zero dependency bloat, and total transparency."
- **The Two-Turn Execution Pattern**:
  1. *Turn 1*: User prompt + Tool Schemas $\to$ Model emits `tool_calls: [{name: 'check_leave_balance', args: {'employee_id': 'EMP-101'}}]`.
  2. *Local Execution*: Backend executes Python function and converts output to JSON.
  3. *Turn 2*: Backend appends `assistant` message with `tool_calls` and `tool` message with JSON output $\to$ Model generates the final natural language answer.

---

## 3. High-Yield Senior Interview Questions & Answers

### Q1: "Why use a Relational DB (MySQL) for documents instead of just a Vector Store?"
> **Strong Answer**:  
> "A Vector Store is an approximate search index (ANN - Approximate Nearest Neighbors), not an enterprise System of Record. 
> 1. **Compliance & Audit**: MySQL gives us ACID compliance, exact upload timestamps, active/superseded status flags, and user access controls.
> 2. **Relational Filtering**: We need hard metadata filtering (e.g. `WHERE entity = 'India' AND effective_date <= '2025-01-01'`) before or alongside semantic retrieval.
> 3. **Cascading Deletions**: Deleting a document in MySQL automatically cascades to all its clauses. In our dual-storage architecture, MySQL represents Truth, while the Vector Store acts as the fast semantic retrieval index."

---

### Q2: "How do you protect your transactional database from AI hallucination or unauthorized modification?"
> **Strong Answer**:  
> "Through three strict defense layers:
> 1. **Read-Only Scoping**: The LLM is only equipped with read-only tools (`lookup_employee_record`, `check_leave_balance`). It has zero write or mutation tools.
> 2. **Contract Enforcing (Pydantic)**: All tool outputs are hydrated into immutable Pydantic schemas (`EmployeeRecord`, `LeaveBalanceResponse`) with range checks (e.g., `grade_band` must be between 1 and 7). If an invalid value is generated, Pydantic raises a `ValidationError` before the model ever sees it.
> 3. **Controlled Escalation**: When human discretion or modification is needed, the model invokes `escalate_to_hrbp`, generating an auditable ticket for a human HRBP rather than attempting to approve leave autonomously."

---

### Q3: "What is the difference between Angular Signals and RxJS Observables, and why use Signals in the chat UI?"
> **Strong Answer**:  
> "Observables represent asynchronous streams of values over time (push-based, cancellable, great for HTTP requests). Signals represent synchronous, trackable values that notify the template of state changes without requiring RxJS subscription management or Zone.js dirty checking.
> In our UI:
> - We use **RxJS `Observable`** in [`PolicyChatService`](file:///C:/Users/StanA/OneDrive/Desktop/Projects/policy-answer-desk/frontend/src/app/core/services/policy-chat.service.ts) for `HttpClient` calls (`http.post()`, `http.get()`).
> - We convert the response into **Signals** (`messages.set()`, `isLoading.set()`) in [`ChatComponent`](file:///C:/Users/StanA/OneDrive/Desktop/Projects/policy-answer-desk/frontend/src/app/components/chat/chat.component.ts) for fine-grained, zoneless reactivity and zero memory leaks."

---

### Q4: "Why did you implement pre-flight token counting with Tiktoken instead of relying on provider usage metrics?"
> **Strong Answer**:  
> "Provider usage metrics are post-flight (you only find out after you've already spent money and incurred latency). By running BPE tokenization locally with `tiktoken` before dispatching requests, we:
> 1. **Prevent Context Overflow**: Catch prompts that exceed context limits before sending them.
> 2. **Enforce Hard Budgets**: Reject requests that violate maximum cost or token thresholds before charging API costs.
> 3. **Measure Latency Accurately**: Calculate tokens-per-second throughput by dividing completion tokens by raw network latency."

---

### Q5: "How does your Markdown clause chunker work, and why not use fixed-size sliding window chunking?"
> **Strong Answer**:  
> "Sliding window chunkers (e.g. 500 tokens with 50-token overlap) blindly cut sentences in half, separating legal qualifications from their parent clauses (e.g., separating 'Annual Leave is 20 days' from 'Provided the employee completed probation').
> In [`document_parser.py`](file:///C:/Users/StanA/OneDrive/Desktop/Projects/policy-answer-desk/backend/app/services/document_parser.py), we implemented **semantic clause chunking** using regex heading boundaries (`(?m)^(#{1,4}\s+.+)$`). This guarantees that each clause, its heading, and its entire conditional body stay intact as a single atomic unit of knowledge, complete with its clause identifier (e.g. `Clause 2: Annual Leave Accrual`)."
