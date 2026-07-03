"""Validated sales-data access and deterministic report generation."""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


DEFAULT_SALES_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "sales.json"
MONEY_PLACES = Decimal("0.01")


class ReportDataError(Exception):
    """Raised when trusted business data cannot be processed safely."""


class SalesRecord(BaseModel):
    """One validated transaction from the mock enterprise data source."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    date: date
    region: str = Field(min_length=2, max_length=50)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class SalesReport(BaseModel):
    """Structured output produced by the report-generation business action."""

    model_config = ConfigDict(extra="forbid")

    period_start: date
    period_end: date
    transaction_count: int = Field(ge=1)
    total_sales: Decimal
    average_sale: Decimal
    sales_by_region: dict[str, Decimal]


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def load_sales_records(data_path: Path = DEFAULT_SALES_DATA_PATH) -> list[SalesRecord]:
    """Load and validate every record without exposing filesystem details."""
    try:
        raw_data: Any = json.loads(data_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReportDataError("Sales data is unavailable or invalid") from error

    if not isinstance(raw_data, list) or not raw_data:
        raise ReportDataError("Sales data is unavailable or invalid")

    try:
        return [SalesRecord.model_validate(item) for item in raw_data]
    except ValidationError as error:
        raise ReportDataError("Sales data is unavailable or invalid") from error


def generate_latest_weekly_sales_report(
    data_path: Path = DEFAULT_SALES_DATA_PATH,
) -> SalesReport:
    """Generate a report for the newest calendar week represented in the data."""
    records = load_sales_records(data_path)
    latest_date = max(record.date for record in records)
    period_start = latest_date - timedelta(days=latest_date.weekday())
    period_end = period_start + timedelta(days=6)
    weekly_records = [
        record for record in records if period_start <= record.date <= period_end
    ]

    total_sales = sum((record.amount for record in weekly_records), Decimal("0"))
    regional_totals: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for record in weekly_records:
        regional_totals[record.region] += record.amount

    return SalesReport(
        period_start=period_start,
        period_end=period_end,
        transaction_count=len(weekly_records),
        total_sales=_money(total_sales),
        average_sale=_money(total_sales / len(weekly_records)),
        sales_by_region={
            region: _money(amount)
            for region, amount in sorted(regional_totals.items())
        },
    )
