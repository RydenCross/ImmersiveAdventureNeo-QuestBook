import json
from pathlib import Path

import pytest

from generator.dependency_license import evaluate_dependency_licenses, write_license_inventory
from generator.dependency_license_contract import run_dependency_license_contract


def test_dependency_license_contract_passes():
    assert run_dependency_license_contract().is_clean


def test_repository_license_policy_is_complete():
    result = evaluate_dependency_licenses(Path("requirements-ci.lock"), Path("dependency-licenses.json"))
    assert result.is_clean
    assert len(result.dependencies) == 15


def test_inventory_write_is_atomic(tmp_path):
    output = write_license_inventory(Path("requirements-ci.lock"), Path("dependency-licenses.json"), tmp_path / "inventory.json")
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "pass"


def test_uncleared_license_is_rejected(tmp_path):
    lock = tmp_path / "lock.txt"
    lock.write_text("alpha==1 --hash=sha256:" + "a" * 64 + "\n", encoding="utf-8")
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"policy":{"allowed_spdx":["MIT"],"denied_spdx":[]},"packages":{"alpha":"Unknown"},"reviewed_exceptions":{}}), encoding="utf-8")
    assert not evaluate_dependency_licenses(lock, policy).is_clean


def test_dirty_policy_cannot_be_written(tmp_path):
    lock = tmp_path / "lock.txt"
    lock.write_text("alpha==1 --hash=sha256:" + "a" * 64 + "\n", encoding="utf-8")
    policy = tmp_path / "policy.json"
    policy.write_text('{"policy":{"allowed_spdx":[],"denied_spdx":[]},"packages":{},"reviewed_exceptions":{}}', encoding="utf-8")
    with pytest.raises(ValueError):
        write_license_inventory(lock, policy, tmp_path / "out.json")
