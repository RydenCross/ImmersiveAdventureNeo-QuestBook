from pathlib import Path

from generator.repository_hygiene import run_repository_hygiene_audit


def _write_complete_gitignore(root: Path) -> None:
    (root / ".gitignore").write_text(
        "\n".join(
            (
                "__pycache__/",
                "*.pyc",
                ".pytest_cache/",
                ".ruff_cache/",
                ".venv/",
                "output/",
                "dist/",
                "build/",
                "*.egg-info/",
                ".env",
                "*.pem",
                "*.key",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_repository_hygiene_is_clean() -> None:
    result = run_repository_hygiene_audit()
    assert result.is_clean
    assert result.forbidden_paths == ()
    assert result.secret_like_paths == ()


def test_hygiene_audit_detects_missing_ignore_patterns(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    result = run_repository_hygiene_audit(tmp_path)
    assert not result.is_clean
    assert "*.pyc" in result.missing_gitignore_patterns


def test_hygiene_audit_detects_secret_like_files(tmp_path: Path) -> None:
    _write_complete_gitignore(tmp_path)
    (tmp_path / ".env.production").write_text("TOKEN=secret\n", encoding="utf-8")
    result = run_repository_hygiene_audit(tmp_path)
    assert ".env.production" in result.secret_like_paths


def test_hygiene_audit_detects_build_artifacts_and_large_files(tmp_path: Path) -> None:
    _write_complete_gitignore(tmp_path)
    (tmp_path / "dist").mkdir()
    (tmp_path / "large.bin").write_bytes(b"x" * 11)
    result = run_repository_hygiene_audit(tmp_path, max_file_bytes=10)
    assert "dist/" in result.forbidden_paths
    assert result.oversized_files


def test_hygiene_audit_json_is_machine_readable() -> None:
    rendered = run_repository_hygiene_audit().format_json()
    assert '"status": "pass"' in rendered
    assert '"forbidden_paths": []' in rendered


def test_hygiene_audit_detects_missing_and_empty_legal_metadata(tmp_path: Path) -> None:
    _write_complete_gitignore(tmp_path)
    (tmp_path / "README.md").write_text("Project\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("Changes\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    result = run_repository_hygiene_audit(tmp_path)
    assert "LICENSE" in result.missing_required_files

    (tmp_path / "LICENSE").write_text("", encoding="utf-8")
    result = run_repository_hygiene_audit(tmp_path)
    assert result.missing_required_files == ()
    assert result.empty_required_files == ("LICENSE",)


def test_hygiene_audit_detects_accidental_command_output(tmp_path: Path) -> None:
    _write_complete_gitignore(tmp_path)
    for name in ("LICENSE", "README.md", "CHANGELOG.md", "pyproject.toml"):
        (tmp_path / name).write_text("present\n", encoding="utf-8")
    (tmp_path / "tatus").write_text("git diff --stat output\n", encoding="utf-8")
    result = run_repository_hygiene_audit(tmp_path)
    assert result.suspicious_command_outputs == ("tatus",)
    assert not result.is_clean
