from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.build import build
from generator.determinism_audit import run_determinism_audit

DEFAULT_OUTPUT_MANIFEST_PATH = Path("reports/generated-output-manifest.json")


@dataclass(frozen=True, slots=True)
class OutputFile:
    path: str
    size: int
    sha256: str

    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "size": self.size, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class OutputManifest:
    file_count: int
    total_bytes: int
    tree_digest: str
    files: tuple[OutputFile, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
            "tree_digest": self.tree_digest,
            "files": [file.to_dict() for file in self.files],
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True, slots=True)
class OutputManifestGuard:
    baseline_file_count: int
    current_file_count: int
    baseline_tree_digest: str
    current_tree_digest: str
    missing_files: tuple[str, ...]
    unexpected_files: tuple[str, ...]
    changed_files: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.missing_files, self.unexpected_files, self.changed_files))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "baseline_file_count": self.baseline_file_count,
            "current_file_count": self.current_file_count,
            "baseline_tree_digest": self.baseline_tree_digest,
            "current_tree_digest": self.current_tree_digest,
            "missing_files": list(self.missing_files),
            "unexpected_files": list(self.unexpected_files),
            "changed_files": list(self.changed_files),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Generated output manifest guard: {'PASS' if self.is_clean else 'FAIL'}",
            f"Files: {self.current_file_count} current / {self.baseline_file_count} baseline.",
            f"Current tree SHA-256: {self.current_tree_digest}",
            f"Missing files: {len(self.missing_files)}.",
            f"Unexpected files: {len(self.unexpected_files)}.",
            f"Changed files: {len(self.changed_files)}.",
        ]
        lines.extend(f"Missing: {path}" for path in self.missing_files)
        lines.extend(f"Unexpected: {path}" for path in self.unexpected_files)
        lines.extend(f"Changed: {path}" for path in self.changed_files)
        return "\n".join(lines)


def create_output_manifest(root: Path) -> OutputManifest:
    files: list[OutputFile] = []
    tree = sha256()
    total_bytes = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        digest = sha256(data).hexdigest()
        files.append(OutputFile(relative, len(data), digest))
        total_bytes += len(data)
        tree.update(relative.encode("utf-8"))
        tree.update(b"\0")
        tree.update(data)
        tree.update(b"\0")
    return OutputManifest(len(files), total_bytes, tree.hexdigest(), tuple(files))


def build_output_manifest() -> OutputManifest:
    with TemporaryDirectory(prefix="quest-output-manifest-") as tmp:
        output = build(Path(tmp), quiet=True)
        return create_output_manifest(output)


def load_output_manifest(path: Path) -> OutputManifest:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        files = tuple(
            OutputFile(str(item["path"]), int(item["size"]), str(item["sha256"]))
            for item in payload["files"]
        )
        return OutputManifest(
            int(payload["file_count"]),
            int(payload["total_bytes"]),
            str(payload["tree_digest"]),
            files,
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid generated output manifest: {path}") from exc


def compare_output_manifests(
    baseline: OutputManifest, current: OutputManifest
) -> OutputManifestGuard:
    baseline_files = {file.path: file for file in baseline.files}
    current_files = {file.path: file for file in current.files}
    baseline_names = set(baseline_files)
    current_names = set(current_files)
    shared = baseline_names & current_names
    return OutputManifestGuard(
        baseline_file_count=baseline.file_count,
        current_file_count=current.file_count,
        baseline_tree_digest=baseline.tree_digest,
        current_tree_digest=current.tree_digest,
        missing_files=tuple(sorted(baseline_names - current_names)),
        unexpected_files=tuple(sorted(current_names - baseline_names)),
        changed_files=tuple(
            sorted(
                path
                for path in shared
                if baseline_files[path].sha256 != current_files[path].sha256
                or baseline_files[path].size != current_files[path].size
            )
        ),
    )


def run_output_manifest_guard(
    baseline_path: Path = DEFAULT_OUTPUT_MANIFEST_PATH,
) -> OutputManifestGuard:
    return compare_output_manifests(load_output_manifest(baseline_path), build_output_manifest())


def refresh_output_manifest(
    destination: Path = DEFAULT_OUTPUT_MANIFEST_PATH,
) -> OutputManifest:
    determinism = run_determinism_audit()
    if not determinism.is_clean:
        raise ValueError("Refusing to refresh output manifest: determinism audit failed.")
    manifest = build_output_manifest()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(manifest.format_json() + "\n", encoding="utf-8")
    return manifest
