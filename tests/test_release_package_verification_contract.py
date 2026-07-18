import json
from pathlib import Path

from generator.release_package_verification_contract import run_release_package_verification_contract


def test_release_package_verification_contract_is_clean() -> None:
    result = run_release_package_verification_contract()
    assert result.is_clean
    assert result.artifact_entries_match
    assert result.artifact_sha256_match
    assert result.reproducibility_entries_match
    assert result.reproducibility_tree_match
    assert not result.forbidden_entries


def test_release_package_verification_json_is_machine_readable() -> None:
    payload = json.loads(run_release_package_verification_contract().format_json())
    assert payload["status"] == "pass"
    assert len(payload["archive_sha256"]) == 64
    assert len(payload["tree_sha256"]) == 64
