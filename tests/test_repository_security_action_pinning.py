from pathlib import Path

from generator.repository_security import validate_workflow_permissions


def test_repository_workflows_use_immutable_action_revisions() -> None:
    assert validate_workflow_permissions() == ()


def test_mutable_action_tag_is_rejected(tmp_path: Path) -> None:
    workflow = tmp_path / "unsafe.yml"
    workflow.write_text("steps:\n  - uses: actions/checkout@v4\n", encoding="utf-8")
    errors = validate_workflow_permissions(tmp_path)
    assert errors == (
        "unsafe.yml: action must be pinned to a full 40-character commit SHA: actions/checkout@v4",
    )


def test_full_action_sha_is_accepted(tmp_path: Path) -> None:
    workflow = tmp_path / "safe.yml"
    workflow.write_text(
        "steps:\n  - uses: actions/checkout@" + "a" * 40 + " # v4\n",
        encoding="utf-8",
    )
    assert validate_workflow_permissions(tmp_path) == ()


def test_dependabot_tracks_github_actions() -> None:
    text = Path(".github/dependabot.yml").read_text(encoding="utf-8")
    assert "package-ecosystem: github-actions" in text
    assert "interval: weekly" in text
