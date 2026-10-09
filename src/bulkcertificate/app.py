from contextlib import asynccontextmanager

from fastapi import FastAPI

from bulkcertificate.db.database import create_tables
from bulkcertificate.api.routes.jobs import router as jobs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager — create database tables on startup."""
    create_tables()
    yield


app = FastAPI(
    title="Bulk Certificate Generator",
    version="0.1.0",
    lifespan=lifespan,
)

# Register routes
app.include_router(jobs_router)


@app.get("/api/v1/health", tags=["health"])
def health_check():
    """Simple health endpoint."""
    return {"status": "ok"}
