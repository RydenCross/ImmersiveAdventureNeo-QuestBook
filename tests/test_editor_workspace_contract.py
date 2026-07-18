from __future__ import annotations

import json

from generator.editor_workspace_contract import run_editor_workspace_contract


def test_editor_workspace_contract_is_clean() -> None:
    result = run_editor_workspace_contract()
    assert result.is_clean, result.format()


def test_editor_workspace_contract_json_is_machine_readable() -> None:
    payload = json.loads(run_editor_workspace_contract().format_json())
    assert payload["status"] == "pass"
    assert payload["deterministic_layout"] is True
