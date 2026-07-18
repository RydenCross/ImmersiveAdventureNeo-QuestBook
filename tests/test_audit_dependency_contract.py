from generator.audit_dependency_contract import run_audit_dependency_contract


def test_repository_audit_dependency_contract_is_clean() -> None:
    result = run_audit_dependency_contract()
    assert result.is_clean
    assert result.registered_audits == 49
    assert result.dependency_cycles == ()


def test_dependency_contract_detects_unknown_and_cycle() -> None:
    result = run_audit_dependency_contract({"release guard": ("missing",), "missing": ("release guard",)})
    assert not result.is_clean
    assert "missing" in result.unknown_dependencies


def test_dependency_contract_json_is_machine_readable() -> None:
    rendered = run_audit_dependency_contract().format_json()
    assert '"status": "pass"' in rendered
    assert '"dependencies"' in rendered
