"""FastAPI application for ARM UI."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.routers import (
    arm_actions,
    dashboard,
    drives,
    jobs,
    logs,
    notifications,
    settings,
    transcoder,
)
from backend.services import arm_client, transcoder_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await arm_client.close_client()
    await transcoder_client.close_client()


app = FastAPI(title="ARM UI", version="1.0.0", lifespan=lifespan)

# CORS for dev (SvelteKit on :5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(dashboard.router)
app.include_router(jobs.router)
app.include_router(arm_actions.router)
app.include_router(transcoder.router)
app.include_router(drives.router)
app.include_router(logs.router)
app.include_router(settings.router)
app.include_router(notifications.router)

# Serve static frontend build if it exists
static_dir = Path(__file__).parent.parent / "frontend" / "build"
if static_dir.is_dir():
    # Serve _app assets directly
    app.mount("/_app", StaticFiles(directory=str(static_dir / "_app")), name="static")

    # SPA catch-all: serve index.html for any non-API route
    @app.get("/{path:path}")
    async def spa_fallback(request: Request):
        return FileResponse(static_dir / "index.html")


if __name__ == "__main__":
    import uvicorn

    from backend.config import settings as cfg

    uvicorn.run("backend.main:app", host="0.0.0.0", port=cfg.port, reload=True)
