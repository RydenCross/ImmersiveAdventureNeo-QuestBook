import json
from pathlib import Path

import pytest

from generator.dependency_security import (
    dependency_inventory,
    evaluate_pip_audit_report,
    load_declared_dependencies,
    write_dependency_inventory,
)
from generator.dependency_security_contract import run_dependency_security_contract


def test_dependency_security_contract_passes():
    assert run_dependency_security_contract().is_clean


def test_inventory_is_deterministic_and_grouped(tmp_path: Path):
    first = dependency_inventory()
    second = dependency_inventory()
    assert first == second
    assert first["dependency_count"] == len(load_declared_dependencies())
    output = write_dependency_inventory(tmp_path / "inventory.json")
    assert json.loads(output.read_text(encoding="utf-8")) == first


def test_policy_detects_and_can_explicitly_ignore_vulnerability(tmp_path: Path):
    report = tmp_path / "audit.json"
    report.write_text(json.dumps({"dependencies": [{"name": "demo", "version": "1.0", "vulns": [{"id": "CVE-2026-1234", "fix_versions": ["1.1"]}]}]}), encoding="utf-8")
    assert not evaluate_pip_audit_report(report).is_clean
    assert evaluate_pip_audit_report(report, ["CVE-2026-1234"]).is_clean


def test_policy_rejects_malformed_report(tmp_path: Path):
    report = tmp_path / "audit.json"
    report.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        evaluate_pip_audit_report(report)
