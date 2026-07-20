from pathlib import Path

from generator.repository_security import validate_workflow_commands


def test_repository_workflow_commands_are_structurally_valid() -> None:
    assert validate_workflow_commands() == ()


def test_indented_command_after_single_line_run_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "broken.yml").write_text(
        "steps:\n  - run: python -m generator first\n      python -m generator second\n",
        encoding="utf-8",
    )
    assert validate_workflow_commands(tmp_path) == (
        "broken.yml:3: indented command follows a single-line run value; use a block scalar",
    )


def test_multiline_run_block_is_accepted(tmp_path: Path) -> None:
    (tmp_path / "safe.yml").write_text(
        "steps:\n  - run: |\n      python -m generator first\n      python -m generator second\n",
        encoding="utf-8",
    )
    assert validate_workflow_commands(tmp_path) == ()
