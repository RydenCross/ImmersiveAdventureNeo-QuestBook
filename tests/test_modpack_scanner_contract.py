import json

from generator.modpack_scanner_contract import run_modpack_scanner_contract


def test_modpack_scanner_contract_is_clean() -> None:
    result = run_modpack_scanner_contract()
    assert result.is_clean
    assert result.modrinth_detected
    assert result.curseforge_detected
    assert result.neoforge_jar_resolved


def test_modpack_scanner_contract_json_is_machine_readable() -> None:
    payload = json.loads(run_modpack_scanner_contract().format_json())
    assert payload["status"] == "pass"
    assert payload["corrupt_archive_rejected"] is True
