from __future__ import annotations

import subprocess

from generator.release_source_validation import validate_release_source


def _runner(commit: str, returncode: int = 0):
    def run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], returncode, stdout=commit + "\n", stderr="")
    return run


def test_release_source_accepts_matching_tag_commit() -> None:
    sha = "a" * 40
    assert validate_release_source("v1.2.3", sha, runner=_runner(sha)).is_clean


def test_release_source_rejects_mismatched_tag_commit() -> None:
    result = validate_release_source("v1.2.3", "a" * 40, runner=_runner("b" * 40))
    assert not result.is_clean
    assert "not source commit" in result.errors[0]


def test_release_source_rejects_invalid_tag_without_git_call() -> None:
    called = False
    def runner(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError
    result = validate_release_source("release-latest", "a" * 40, runner=runner)
    assert not result.is_clean
    assert not called


def test_release_source_rejects_unresolvable_tag() -> None:
    result = validate_release_source("v1.2.3", "a" * 40, runner=_runner("", 1))
    assert not result.is_clean
    assert "cannot resolve" in result.errors[0]
