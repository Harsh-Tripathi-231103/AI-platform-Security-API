"""FastAPI application entry point."""

from uuid import uuid4

from fastapi import FastAPI
from fastapi import Request

from app.api.ask import router as ask_router
from app.core.audit import configure_logging, reset_request_id, set_request_id
from app.core.config import get_settings


settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="A security-first enterprise AI workflow API.",
)
app.include_router(ask_router)


@app.middleware("http")
async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Assign an untrusted-client-independent correlation ID to every request."""
    request_id = str(uuid4())
    token = set_request_id(request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        reset_request_id(token)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Return a minimal liveness response without exposing configuration."""
    return {"status": "healthy"}
