from pathlib import Path

import pytest

from generator.github_release import create_github_release_plan, publish_github_release


def test_release_plan_is_deterministic_and_dry_run_is_safe(tmp_path: Path) -> None:
    notes = tmp_path / "notes.md"; notes.write_text("notes", encoding="utf-8")
    artifact = tmp_path / "app.zip"; artifact.write_bytes(b"payload")
    plan = create_github_release_plan("owner/repo", "v1.0.0", [artifact], notes_file=notes)
    assert plan.assets[0].sha256
    assert not publish_github_release(plan).executed


def test_release_plan_rejects_bad_repository(tmp_path: Path) -> None:
    notes = tmp_path / "notes.md"; notes.write_text("notes", encoding="utf-8")
    artifact = tmp_path / "app.zip"; artifact.write_bytes(b"payload")
    with pytest.raises(ValueError):
        create_github_release_plan("owner", "v1.0.0", [artifact], notes_file=notes)
