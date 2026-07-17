from dataclasses import dataclass

from generator.quality_gate import run_checks, run_quality_gate


@dataclass(frozen=True)
class StubResult:
    is_clean: bool


def test_quality_gate_passes_when_all_checks_are_clean() -> None:
    result = run_checks({"one": lambda: StubResult(True), "two": lambda: StubResult(True)})
    assert result.is_clean
    assert result.passed_count == 2
    assert result.failed_checks == ()


def test_quality_gate_reports_failed_checks() -> None:
    result = run_checks({"clean": lambda: StubResult(True), "broken": lambda: StubResult(False)})
    assert not result.is_clean
    assert result.failed_checks == ("broken",)
    assert '"status": "fail"' in result.format_json()


def test_quality_gate_converts_runner_errors_to_failures() -> None:
    def broken() -> StubResult:
        raise ValueError("bad baseline")

    result = run_checks({"broken": broken})
    assert not result.is_clean
    assert result.checks[0].detail == "error: bad baseline"


def test_quality_gate_text_lists_each_check() -> None:
    result = run_checks({"one": lambda: StubResult(True)})
    assert "Quality gate: PASS" in result.format()
    assert "[PASS] one: clean" in result.format()


def test_repository_quality_gate_is_clean() -> None:
    result = run_quality_gate()
    assert result.is_clean
    assert len(result.checks) == 23
