import json

from generator.report_determinism_contract import (
    ReportDeterminismContract,
    run_report_determinism_contract,
)


def test_repository_reports_are_deterministic() -> None:
    result = run_report_determinism_contract()
    assert result.is_clean
    assert result.checked_reports == 43
    assert len(result.deterministic_reports) == 43


def test_contract_detects_nondeterministic_reports() -> None:
    result = ReportDeterminismContract(
        checked_reports=1,
        deterministic_reports=(),
        nondeterministic_reports=("unstable.json",),
        invalid_reports=(),
    )
    assert not result.is_clean
    assert "Nondeterministic: unstable.json" in result.format()


def test_contract_json_is_machine_readable() -> None:
    payload = json.loads(run_report_determinism_contract().format_json())
    assert payload["status"] == "pass"
    assert payload["nondeterministic_reports"] == []
