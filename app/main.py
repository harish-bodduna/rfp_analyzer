"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import documents
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title="RFP Analyzer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(documents.router, prefix="/documents", tags=["documents"])


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
