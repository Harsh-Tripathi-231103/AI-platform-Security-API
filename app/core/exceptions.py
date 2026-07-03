"""Centralized exception handling that prevents sensitive error disclosure."""

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.audit import AuditEvent, get_request_id, record_audit_event
from app.models.schemas import ErrorDetail, ErrorResponse


application_logger = logging.getLogger("application.error")

ERROR_CODES = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_401_UNAUTHORIZED: "authentication_failed",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "invalid_request",
    status.HTTP_429_TOO_MANY_REQUESTS: "rate_limit_exceeded",
    status.HTTP_503_SERVICE_UNAVAILABLE: "service_unavailable",
}


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=get_request_id(),
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(),
        headers=headers,
    )


async def http_exception_handler(
    request: Request,
    exception: HTTPException,
) -> JSONResponse:
    """Return controlled HTTP failures without framework-specific details."""
    del request
    message = exception.detail if isinstance(exception.detail, str) else "Request failed"
    return _error_response(
        status_code=exception.status_code,
        code=ERROR_CODES.get(exception.status_code, "request_failed"),
        message=message,
        headers=exception.headers,
    )


async def validation_exception_handler(
    request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    """Reject malformed input without echoing values or internal schema details."""
    del request, exception
    record_audit_event(
        AuditEvent.REQUEST_REJECTED,
        outcome="failure",
        reason="validation_failed",
    )
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="invalid_request",
        message="Request validation failed",
    )


async def unhandled_exception_handler(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Record an internal failure while returning no implementation details."""
    del request
    request_id = get_request_id()
    record_audit_event(
        AuditEvent.INTERNAL_ERROR,
        outcome="failure",
        reason="unhandled_exception",
    )
    application_logger.error(
        "Unhandled application exception request_id=%s type=%s",
        request_id,
        type(exception).__name__,
    )
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="internal_error",
        message="An unexpected error occurred",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Install all API exception handlers in one place."""
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
