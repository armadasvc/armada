from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import bot_router

app = FastAPI(
    title="Armada Orchestrator API",
    description="Orchestration API for agents and Kubernetes jobs",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(bot_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
