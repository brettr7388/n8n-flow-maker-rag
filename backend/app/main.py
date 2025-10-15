"""
Main FastAPI application for n8n workflow generator.
Enhanced with conversation-based workflow generation.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .routers import generate, validate, conversation

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="n8n Flow Generator API",
    description="Generate production-ready n8n workflows from natural language using AI with interactive questioning",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(generate.router, prefix="/api", tags=["generation"])
app.include_router(validate.router, prefix="/api", tags=["validation"])
app.include_router(conversation.router, prefix="/api/conversation", tags=["conversation"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "n8n Flow Generator API v2.0",
        "version": "2.0.0",
        "features": [
            "Interactive conversation-based workflow generation",
            "Complex workflow generation (10-20+ nodes)",
            "Production-ready workflows with error handling",
            "Data validation and duplicate checking",
            "Pattern library and node catalog",
            "RAG-enhanced generation"
        ],
        "docs": "/docs",
        "endpoints": {
            "simple_generation": "/api/generate",
            "conversation_start": "/api/conversation/start",
            "conversation_answer": "/api/conversation/answer",
            "conversation_generate": "/api/conversation/generate"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

