"""Tests for the sales-report business action."""

from decimal import Decimal
from pathlib import Path

import pytest

from app.services.report_service import (
    DEFAULT_SALES_DATA_PATH,
    ReportDataError,
    generate_latest_weekly_sales_report,
    load_sales_records,
)


def test_generates_latest_week_report_from_mock_data() -> None:
    report = generate_latest_weekly_sales_report()

    assert report.period_start.isoformat() == "2026-06-29"
    assert report.period_end.isoformat() == "2026-07-05"
    assert report.transaction_count == 6
    assert report.total_sales == Decimal("5000.00")
    assert report.average_sale == Decimal("833.33")
    assert report.sales_by_region == {
        "East": Decimal("799.50"),
        "North": Decimal("1600.50"),
        "South": Decimal("1100.00"),
        "West": Decimal("1500.00"),
    }


def test_default_mock_data_is_valid() -> None:
    records = load_sales_records(DEFAULT_SALES_DATA_PATH)

    assert len(records) == 7


@pytest.mark.parametrize(
    "content",
    [
        "not-json",
        "[]",
        '[{"date":"invalid","region":"North","amount":"5.00"}]',
        '[{"date":"2026-07-03","region":"N","amount":"5.00"}]',
        '[{"date":"2026-07-03","region":"North","amount":"-5.00"}]',
    ],
)
def test_rejects_invalid_business_data(tmp_path: Path, content: str) -> None:
    data_path = tmp_path / "sales.json"
    data_path.write_text(content, encoding="utf-8")

    with pytest.raises(ReportDataError, match="Sales data is unavailable or invalid"):
        generate_latest_weekly_sales_report(data_path)


def test_rejects_missing_business_data(tmp_path: Path) -> None:
    with pytest.raises(ReportDataError, match="Sales data is unavailable or invalid"):
        generate_latest_weekly_sales_report(tmp_path / "missing.json")
