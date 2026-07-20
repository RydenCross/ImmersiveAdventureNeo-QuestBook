from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from generator.release_artifact_audit import run_release_artifact_audit
from generator.release_reproducibility_audit import _build_archive, run_release_reproducibility_audit


@dataclass(frozen=True, slots=True)
class ReleasePackageVerificationContract:
    archive_entries: int
    archive_sha256: str
    tree_sha256: str
    artifact_entries_match: bool
    artifact_sha256_match: bool
    reproducibility_entries_match: bool
    reproducibility_tree_match: bool
    forbidden_entries: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return (
            self.artifact_entries_match
            and self.artifact_sha256_match
            and self.reproducibility_entries_match
            and self.reproducibility_tree_match
            and not self.forbidden_entries
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "archive_entries": self.archive_entries,
            "archive_sha256": self.archive_sha256,
            "tree_sha256": self.tree_sha256,
            "artifact_entries_match": self.artifact_entries_match,
            "artifact_sha256_match": self.artifact_sha256_match,
            "reproducibility_entries_match": self.reproducibility_entries_match,
            "reproducibility_tree_match": self.reproducibility_tree_match,
            "forbidden_entries": list(self.forbidden_entries),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Release package verification contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Archive entries: {self.archive_entries}.",
            f"Artifact entry count matches: {'yes' if self.artifact_entries_match else 'no'}.",
            f"Artifact SHA-256 matches: {'yes' if self.artifact_sha256_match else 'no'}.",
            f"Reproducibility entry count matches: {'yes' if self.reproducibility_entries_match else 'no'}.",
            f"Reproducibility tree hash matches: {'yes' if self.reproducibility_tree_match else 'no'}.",
            f"Forbidden entries: {len(self.forbidden_entries)}.",
        ))


def run_release_package_verification_contract(root: Path = Path('.')) -> ReleasePackageVerificationContract:
    root = root.resolve()
    artifact = run_release_artifact_audit(root)
    reproducibility = run_release_reproducibility_audit(root)
    with TemporaryDirectory() as temporary_directory:
        archive_path = Path(temporary_directory) / "release.zip"
        archive_sha256, entry_digests, tree_sha256 = _build_archive(root, archive_path)
        with ZipFile(archive_path) as archive:
            names = tuple(archive.namelist())
    forbidden = tuple(sorted(
        name for name in names
        if any(part in {"__pycache__", ".pytest_cache", ".ruff_cache", ".venv"} or part.endswith(".egg-info") for part in Path(name).parts)
        or name.endswith((".pyc", ".pyo"))
    ))
    return ReleasePackageVerificationContract(
        archive_entries=len(entry_digests),
        archive_sha256=archive_sha256,
        tree_sha256=tree_sha256,
        artifact_entries_match=artifact.archive_entries == len(entry_digests),
        artifact_sha256_match=artifact.archive_sha256 == archive_sha256,
        reproducibility_entries_match=reproducibility.archive_entries == len(entry_digests),
        reproducibility_tree_match=(
            reproducibility.first_tree_sha256 == tree_sha256
            and reproducibility.second_tree_sha256 == tree_sha256
        ),
        forbidden_entries=forbidden,
    )
