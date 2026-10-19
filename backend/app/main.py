"""
Module: main.py
Responsibility: FastAPI ASGI Application entry point for Policy Answer Desk.
Configures:
- CORS middleware for Angular frontend (localhost:4200).
- Modular API routers for tools, chat, and document management.
- Structured exception handlers.
- Auto-generated OpenAPI / Swagger docs.
"""

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine, Base
import app.db.document

# Automatically create tables in MySQL if they do not exist
Base.metadata.create_all(bind=engine)
from app.routers import chat, tools, document, mcp, traces

# Initialize FastAPI app
app = FastAPI(
    title="Policy Answer Desk API",
    description="Backend API for HR Policy RAG & Agentic AI Assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",  # Angular default dev server
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health & Diagnostic Endpoints ---
@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Returns application health status."""
    return {"status": "healthy", "service": "policy-answer-desk-backend"}


# --- API v1 Modular Router Hierarchy ---
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(tools.router)
api_v1_router.include_router(chat.router)
api_v1_router.include_router(document.router)
api_v1_router.include_router(mcp.router)
api_v1_router.include_router(traces.router)

app.include_router(api_v1_router)