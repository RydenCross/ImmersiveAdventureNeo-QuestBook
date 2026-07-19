from generator.audit_performance_contract import run_audit_performance_contract


def test_repository_audit_performance_contract_is_clean() -> None:
    result = run_audit_performance_contract()
    assert result.is_clean
    assert result.registered_audits == 62
    assert result.timed_audits == 62
    assert result.duplicate_executions == ()


def test_audit_performance_contract_detects_budget_failure() -> None:
    ticks = iter((0.0, 0.020))
    result = run_audit_performance_contract(
        {"probe": lambda: None}, budget_ms=10.0, clock=lambda: next(ticks)
    )
    assert not result.is_clean
    assert result.over_budget


def test_audit_performance_contract_json_is_machine_readable() -> None:
    rendered = run_audit_performance_contract().format_json()
    assert '"status": "pass"' in rendered
    assert '"slowest_audits"' in rendered
