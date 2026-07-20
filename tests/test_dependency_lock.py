from pathlib import Path

import pytest

from generator.dependency_lock import (
    parse_hashed_lock,
    reproducible_install_plan,
    write_lock_manifest,
)
from generator.dependency_lock_contract import run_dependency_lock_contract


def test_dependency_lock_contract_passes():
    assert run_dependency_lock_contract().is_clean


def test_lock_rejects_ranges(tmp_path: Path):
    path = tmp_path / "requirements.lock"
    path.write_text("pytest>=8\n", encoding="utf-8")
    with pytest.raises(ValueError):
        parse_hashed_lock(path)


def test_install_plan_requires_hashes_and_no_dependencies(tmp_path: Path):
    path = tmp_path / "requirements.lock"
    path.write_text("pytest==8.4.1 --hash=sha256:" + "a" * 64 + "\n", encoding="utf-8")
    plan = reproducible_install_plan(path)
    assert "--require-hashes" in plan
    assert "--no-deps" in plan
    assert "--only-binary=:all:" in plan


def test_manifest_write_is_atomic(tmp_path: Path):
    path = tmp_path / "requirements.lock"
    path.write_text("pytest==8.4.1 --hash=sha256:" + "a" * 64 + "\n", encoding="utf-8")
    output = write_lock_manifest(path, tmp_path / "nested" / "manifest.json")
    assert output.is_file()
    assert not output.with_name(output.name + ".tmp").exists()
