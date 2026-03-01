"""
Point d'entree FastAPI.

Lancement :
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.events import router as events_router, ws_router
from app.routers.jobs import router as jobs_router
from app.routers.runs import router as runs_router


app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080","http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(events_router)
app.include_router(jobs_router)
app.include_router(runs_router)
app.include_router(ws_router)
