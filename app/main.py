"""FastAPI application entry point."""

from fastapi import FastAPI

from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="A security-first enterprise AI workflow API.",
)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Return a minimal liveness response without exposing configuration."""
    return {"status": "healthy"}

