from pathlib import Path

from generator.packaging_audit import run_packaging_audit


def test_repository_packaging_configuration_is_clean() -> None:
    result = run_packaging_audit()
    assert result.is_clean
    assert result.console_script == "generator.cli:main"


def test_packaging_audit_reports_missing_configuration(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "broken"\n', encoding="utf-8")
    result = run_packaging_audit(path)
    assert not result.is_clean
    assert any("content*" in error for error in result.errors)


def test_packaging_audit_json_is_machine_readable() -> None:
    assert '"status": "pass"' in run_packaging_audit().format_json()
