from generator.audit_registry_contract import AUDIT_REGISTRY, run_audit_registry_contract


def test_audit_registry_contract_is_clean() -> None:
    result = run_audit_registry_contract()
    assert result.is_clean
    assert result.registrations == 54


def test_audit_registry_identifiers_are_unique() -> None:
    assert len({item.gate_name for item in AUDIT_REGISTRY}) == len(AUDIT_REGISTRY)
    assert len({item.command for item in AUDIT_REGISTRY}) == len(AUDIT_REGISTRY)
    reports = [item.report for item in AUDIT_REGISTRY if item.report]
    assert len(set(reports)) == len(reports)


def test_audit_registry_json_is_machine_readable() -> None:
    result = run_audit_registry_contract()
    assert '"status": "pass"' in result.format_json()
