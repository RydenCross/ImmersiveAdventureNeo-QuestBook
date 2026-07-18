from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

DEFAULT_ROOT = Path(".")
DEFAULT_MANIFEST_PATH = Path("reports/generated-output-manifest.json")
_IGNORED_PARTS = {".git", ".pytest_cache", ".ruff_cache", ".venv", "__pycache__"}
_IGNORED_SUFFIXES = {".pyc", ".pyo"}
_EXCLUDED_REPORTS = {
    "reports/release-artifact-audit.json",
    "reports/release-reproducibility-audit.json",
    "reports/release-package-verification-audit.json",
    "reports/release-manifest-audit.json",
    "reports/release-archive-metadata-audit.json",
    "reports/quality-gate.json",
    "reports/report-freshness-guard.json",
}


@dataclass(frozen=True, slots=True)
class ReleaseArtifactAudit:
    archive_entries: int
    archive_bytes: int
    archive_sha256: str
    duplicate_entries: tuple[str, ...]
    invalid_json_files: tuple[str, ...]
    empty_files: tuple[str, ...]
    missing_generated_files: tuple[str, ...]
    forbidden_entries: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any(
            (
                self.duplicate_entries,
                self.invalid_json_files,
                self.empty_files,
                self.missing_generated_files,
                self.forbidden_entries,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "archive_entries": self.archive_entries,
            "archive_bytes": self.archive_bytes,
            "archive_sha256": self.archive_sha256,
            "duplicate_entries": list(self.duplicate_entries),
            "invalid_json_files": list(self.invalid_json_files),
            "empty_files": list(self.empty_files),
            "missing_generated_files": list(self.missing_generated_files),
            "forbidden_entries": list(self.forbidden_entries),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Release artifact audit: {'PASS' if self.is_clean else 'FAIL'}",
                f"Archive entries: {self.archive_entries}.",
                f"Archive bytes: {self.archive_bytes}.",
                f"Duplicate entries: {len(self.duplicate_entries)}.",
                f"Invalid JSON files: {len(self.invalid_json_files)}.",
                f"Empty files: {len(self.empty_files)}.",
                f"Missing generated files: {len(self.missing_generated_files)}.",
                f"Forbidden entries: {len(self.forbidden_entries)}.",
                f"Archive SHA-256: {self.archive_sha256}.",
            )
        )


def _release_files(root: Path) -> tuple[Path, ...]:
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative.as_posix() in _EXCLUDED_REPORTS:
            continue
        if any(part in _IGNORED_PARTS or part.endswith(".egg-info") for part in relative.parts):
            continue
        if path.suffix.lower() in _IGNORED_SUFFIXES:
            continue
        files.append(path)
    return tuple(files)



def _write_release_archive(root: Path, destination: Path) -> tuple[Path, ...]:
    files = _release_files(root)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            name = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return files

def run_release_artifact_audit(
    root: Path = DEFAULT_ROOT,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> ReleaseArtifactAudit:
    root = root.resolve()
    with tempfile.TemporaryDirectory() as temp_dir:
        archive_path = Path(temp_dir) / "release.zip"
        files = _write_release_archive(root, archive_path)
        archive_bytes = archive_path.read_bytes()
        digest = hashlib.sha256(archive_bytes).hexdigest()
        with zipfile.ZipFile(archive_path) as archive:
            names = archive.namelist()
            duplicate_entries = tuple(sorted({name for name in names if names.count(name) > 1}))
            invalid_json = []
            empty = []
            forbidden = []
            for info in archive.infolist():
                name = info.filename
                if info.file_size == 0 and name.startswith(("output/", "reports/")):
                    empty.append(name)
                if any(
                    part in _IGNORED_PARTS or part.endswith(".egg-info")
                    for part in Path(name).parts
                ):
                    forbidden.append(name)
                if name.endswith((".pyc", ".pyo")):
                    forbidden.append(name)
                if name.endswith(".json"):
                    try:
                        json.loads(archive.read(info).decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        invalid_json.append(name)

    missing_generated = []
    try:
        manifest = json.loads((root / manifest_path).read_text(encoding="utf-8"))
        expected = manifest.get("files", {})
        expected_names = expected.keys() if isinstance(expected, dict) else ()
        release_names = {path.relative_to(root).as_posix() for path in files}
        for name in expected_names:
            if name not in release_names and f"output/{name}" not in release_names:
                missing_generated.append(str(name))
    except (OSError, json.JSONDecodeError, TypeError):
        missing_generated.append(manifest_path.as_posix())

    return ReleaseArtifactAudit(
        archive_entries=len(files),
        archive_bytes=len(archive_bytes),
        archive_sha256=digest,
        duplicate_entries=duplicate_entries,
        invalid_json_files=tuple(sorted(invalid_json)),
        empty_files=tuple(sorted(empty)),
        missing_generated_files=tuple(sorted(missing_generated)),
        forbidden_entries=tuple(sorted(set(forbidden))),
    )
