from pathlib import Path

from generator.cli_audit import EXPECTED_COMMANDS
from generator.documentation_audit import run_documentation_audit


def test_repository_documentation_contract_is_clean() -> None:
    result = run_documentation_audit()
    assert result.is_clean
    assert result.missing_command_docs == ()
    assert result.broken_links == ()


def test_documentation_audit_detects_missing_command_docs(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    docs = tmp_path / "docs"
    docs.mkdir()
    readme.write_text("# Minimal\n", encoding="utf-8")
    result = run_documentation_audit(readme, docs)
    assert not result.is_clean
    assert "quality-gate" in result.missing_command_docs


def test_documentation_audit_detects_broken_links(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    docs = tmp_path / "docs"
    docs.mkdir()
    commands = "\n".join(f"python -m generator {command}" for command in EXPECTED_COMMANDS)
    readme.write_text(commands + "\n[Missing](docs/MISSING.md)\n", encoding="utf-8")
    assert run_documentation_audit(readme, docs).broken_links


def test_documentation_audit_json_is_machine_readable() -> None:
    rendered = run_documentation_audit().format_json()
    assert '"status": "pass"' in rendered
    assert '"broken_links": []' in rendered
