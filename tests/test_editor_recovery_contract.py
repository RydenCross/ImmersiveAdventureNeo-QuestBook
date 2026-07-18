from __future__ import annotations

import json

from generator.editor_recovery_contract import run_editor_recovery_contract


def test_editor_recovery_contract_is_clean() -> None:
    result = run_editor_recovery_contract()
    assert result.is_clean, result.format()


def test_editor_recovery_contract_json_is_machine_readable() -> None:
    payload = json.loads(run_editor_recovery_contract().format_json())
    assert payload["status"] == "pass"
    assert payload["autosave_after_edit"] is True
    assert payload["snapshot_round_trip"] is True
