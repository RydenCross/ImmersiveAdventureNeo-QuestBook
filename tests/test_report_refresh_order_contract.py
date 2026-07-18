from generator.report_refresh_order_contract import (
    ARCHIVE_DERIVED_REPORTS,
    run_report_refresh_order_contract,
)
from generator.report_freshness import report_refresh_order


def test_report_refresh_order_contract_is_clean() -> None:
    result = run_report_refresh_order_contract()
    assert result.is_clean
    assert result.missing_archive_reports == ()
    assert result.archive_reports_not_last == ()


def test_archive_derived_reports_are_last() -> None:
    order = report_refresh_order()
    assert order[-len(ARCHIVE_DERIVED_REPORTS):] == ARCHIVE_DERIVED_REPORTS


def test_report_refresh_order_serializes_status() -> None:
    payload = run_report_refresh_order_contract().to_dict()
    assert payload["status"] == "pass"
    assert payload["duplicate_reports"] == []
