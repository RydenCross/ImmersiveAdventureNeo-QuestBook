from pathlib import Path
from unittest.mock import patch

import pytest

from generator.output_writer import atomic_write_text
from generator.report_write_safety_contract import run_report_write_safety_contract


def test_report_write_safety_contract_is_clean() -> None:
    result = run_report_write_safety_contract()
    assert result.is_clean
    assert result.direct_cli_writes == ()


def test_atomic_write_preserves_existing_file_on_replace_failure(tmp_path: Path) -> None:
    destination = tmp_path / "report.json"
    destination.write_text("original\n", encoding="utf-8")
    with patch("generator.output_writer.os.replace", side_effect=OSError("blocked")):
        with pytest.raises(OSError):
            atomic_write_text(destination, "replacement\n")
    assert destination.read_text(encoding="utf-8") == "original\n"
    assert tuple(tmp_path.iterdir()) == (destination,)


def test_report_write_safety_serializes_status() -> None:
    payload = run_report_write_safety_contract().to_dict()
    assert payload["status"] == "pass"
    assert payload["temporary_files_left_behind"] == []
