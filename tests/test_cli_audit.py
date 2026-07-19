from pathlib import Path

from generator.cli_audit import EXPECTED_COMMANDS, run_cli_audit


def test_repository_cli_contract_is_clean() -> None:
    result = run_cli_audit()
    assert result.is_clean
    assert result.commands == tuple(sorted(EXPECTED_COMMANDS))
    assert result.console_script == "generator.cli:main"


def test_cli_audit_reports_broken_console_script(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text(
        '[project]\nname = "broken"\n[project.scripts]\n'
        'immersive-adventure-quests = "broken:main"\n',
        encoding="utf-8",
    )
    result = run_cli_audit(path)
    assert not result.is_clean
    assert result.errors


def test_cli_audit_json_is_machine_readable() -> None:
    rendered = run_cli_audit().format_json()
    assert '"status": "pass"' in rendered
    assert '"command_count": 82' in rendered
