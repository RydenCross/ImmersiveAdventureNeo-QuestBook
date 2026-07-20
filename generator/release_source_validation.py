from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
from typing import Callable, Sequence

_TAG = re.compile(r"^v\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
_SHA = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True, slots=True)
class ReleaseSourceValidation:
    tag: str
    tag_commit: str | None
    source_commit: str
    errors: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "tag": self.tag,
            "tag_commit": self.tag_commit,
            "source_commit": self.source_commit,
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def validate_release_source(
    tag: str,
    source_commit: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> ReleaseSourceValidation:
    errors: list[str] = []
    if not _TAG.fullmatch(tag):
        errors.append("release tag must be semantic version form vMAJOR.MINOR.PATCH")
    if not _SHA.fullmatch(source_commit):
        errors.append("source commit must be a full lowercase 40-character Git SHA")
    tag_commit: str | None = None
    if not errors:
        completed = runner(
            ["git", "rev-list", "-n", "1", tag],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            errors.append(f"cannot resolve release tag {tag}")
        else:
            candidate = completed.stdout.strip().lower()
            if not _SHA.fullmatch(candidate):
                errors.append(f"release tag {tag} did not resolve to a full Git SHA")
            else:
                tag_commit = candidate
                if candidate != source_commit:
                    errors.append(
                        f"release tag {tag} points to {candidate}, not source commit {source_commit}"
                    )
    return ReleaseSourceValidation(tag, tag_commit, source_commit, tuple(errors))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a release tag matches the checked-out source commit.")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args(argv)
    result = validate_release_source(args.tag, args.source_commit)
    print(result.format_json())
    return 0 if result.is_clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
