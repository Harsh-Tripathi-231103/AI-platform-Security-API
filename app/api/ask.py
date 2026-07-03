"""Authenticated and authorized enterprise question endpoint."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.authorization import Permission, authorize
from app.core.security import AuthenticatedUser, authenticate_api_key
from app.models.schemas import ActionResult, AskRequest, AskResponse
from app.services.intent_service import BusinessIntent, intent_service
from app.services.report_service import (
    ReportDataError,
    generate_latest_weekly_sales_report,
)


router = APIRouter(tags=["enterprise-ai"])


@router.post("/ask", response_model=AskResponse)
def ask_question(
    payload: AskRequest,
    user: Annotated[AuthenticatedUser, Depends(authenticate_api_key)],
) -> AskResponse:
    """Process one authenticated question through the controlled workflow."""
    request_id = str(uuid4())
    decision = intent_service.detect_intent(payload.question)

    if decision.intent is BusinessIntent.UNKNOWN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported business request",
        )

    if decision.intent is BusinessIntent.GENERATE_SALES_REPORT:
        authorize(user, Permission.GENERATE_REPORT)
        try:
            report = generate_latest_weekly_sales_report()
        except ReportDataError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The report service is temporarily unavailable",
            ) from error

        return AskResponse(
            request_id=request_id,
            answer=(
                f"Weekly sales report generated for {report.period_start} through "
                f"{report.period_end}. Total sales were {report.total_sales} across "
                f"{report.transaction_count} transactions."
            ),
            action=ActionResult(
                name=BusinessIntent.GENERATE_SALES_REPORT.value,
                data=report.model_dump(mode="json"),
            ),
        )

    # Defensive default if a new intent is added without an execution branch.
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported business request",
    )
