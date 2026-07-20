from __future__ import annotations

import json

from generator.editor_ui_contract import run_editor_ui_contract


def test_editor_ui_contract_is_clean() -> None:
    result = run_editor_ui_contract()
    assert result.is_clean, result.format()


def test_editor_ui_contract_json_is_machine_readable() -> None:
    payload = json.loads(run_editor_ui_contract().format_json())
    assert payload["status"] == "pass"
    assert payload["http_import"] is True
