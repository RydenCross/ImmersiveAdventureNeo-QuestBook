from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import hashlib
import json
from pathlib import Path
from typing import Any

from generator.output_writer import atomic_write_text

CACHE_VERSION = 1
DEFAULT_CACHE_FILENAME = ".report-refresh-cache.json"
_IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "build",
}
_IGNORED_SUFFIXES = {".pyc", ".pyo"}

_PROJECT_REPORTS = {
    "release-guard.json",
    "dependency-audit.json",
    "progression-metrics.json",
    "progression-guard.json",
    "identity-guard.json",
    "contract-guard.json",
    "reward-audit.json",
    "task-audit.json",
    "chapter-audit.json",
    "text-audit.json",
    "determinism-audit.json",
    "output-manifest-guard.json",
    "mod-compatibility-audit.json",
}
_DOCUMENTATION_REPORTS = {"documentation-audit.json"}
_TEST_REPORTS = {"test-inventory-audit.json"}
_REPORT_META_REPORTS = {
    "report-schema-audit.json",
    "report-consistency-audit.json",
    "report-provenance-audit.json",
    "report-determinism-audit.json",
    "cli-output-audit.json",
    "cli-exit-code-audit.json",
    "report-refresh-idempotence-audit.json",
    "release-report-finalization-audit.json",
}
_REPOSITORY_WIDE_REPORTS = {
    "repository-hygiene-audit.json",
    "release-artifact-audit.json",
    "release-reproducibility-audit.json",
    "release-package-verification-audit.json",
    "release-manifest-audit.json",
    "release-archive-metadata-audit.json",
    "release-archive-extraction-safety-audit.json",
    "release-archive-unicode-path-audit.json",
    "release-archive-compression-audit.json",
}


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_digest(path: Path) -> str | None:
    try:
        return _digest_bytes(path.read_bytes())
    except OSError:
        return None


def _is_ignored(relative: Path, *, cache_path: Path | None = None) -> bool:
    if cache_path is not None:
        try:
            if relative == cache_path:
                return True
        except ValueError:
            pass
    if any(part in _IGNORED_DIRECTORY_NAMES or part.endswith(".egg-info") for part in relative.parts):
        return True
    return relative.suffix.lower() in _IGNORED_SUFFIXES


def _matching_files(
    root: Path,
    patterns: Sequence[str],
    *,
    excluded: set[Path],
) -> tuple[Path, ...]:
    files: set[Path] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if relative in excluded or _is_ignored(relative):
                continue
            files.add(path)
    return tuple(sorted(files, key=lambda item: item.relative_to(root).as_posix()))


def default_input_patterns(report_name: str) -> tuple[str, ...]:
    """Return conservative source scopes for a tracked report.

    All reports depend on generator implementation code. Additional scopes are
    selected by report family so documentation-only or test-only edits do not
    force unrelated content audits to rerun.
    """

    patterns: list[str] = ["generator/**/*.py", "pyproject.toml"]
    if report_name in _PROJECT_REPORTS:
        patterns.extend(("content/**/*.py", "model/**/*.py", "config/**/*.json"))
    if report_name in _DOCUMENTATION_REPORTS:
        patterns.extend(("README.md", "CHANGELOG.md", "docs/**/*.md"))
    if report_name in _TEST_REPORTS:
        patterns.append("tests/**/*.py")
    if report_name in _REPORT_META_REPORTS:
        patterns.extend(("reports/*.json", "tests/**/*.py", "README.md", "docs/**/*.md"))
    if report_name in _REPOSITORY_WIDE_REPORTS:
        patterns.append("**/*")
    if report_name in {"packaging-audit.json", "cli-audit.json"}:
        patterns.extend(("README.md", "docs/**/*.md"))
    if report_name in {
        "audit-registry-audit.json",
        "audit-performance-audit.json",
        "audit-dependency-audit.json",
        "report-refresh-order-audit.json",
        "report-refresh-audit.json",
        "report-refresh-convergence-audit.json",
        "report-write-safety-audit.json",
    }:
        patterns.extend(("tests/**/*.py", "README.md", "docs/**/*.md"))
    return tuple(dict.fromkeys(patterns))


def _report_dependencies(report_name: str) -> tuple[str, ...]:
    # Lazy imports avoid cycles while the report registry is assembled.
    from generator.audit_dependency_contract import AUDIT_DEPENDENCIES
    from generator.audit_registry_contract import AUDIT_REGISTRY

    gate_to_report = {item.gate_name: item.report for item in AUDIT_REGISTRY if item.report}
    report_to_gate = {item.report: item.gate_name for item in AUDIT_REGISTRY if item.report}
    gate_name = report_to_gate.get(report_name)
    if gate_name is None:
        return ()
    return tuple(
        report
        for dependency in AUDIT_DEPENDENCIES.get(gate_name, ())
        if (report := gate_to_report.get(dependency)) is not None
    )


def default_report_fingerprint(
    report_name: str,
    *,
    root: Path,
    report_directory: Path,
    cache_path: Path,
    order: Sequence[str],
) -> str:
    root = root.resolve()
    report_directory = report_directory.resolve()
    cache_path = cache_path.resolve()
    excluded: set[Path] = set()
    for candidate in (cache_path, report_directory / report_name):
        try:
            excluded.add(candidate.relative_to(root))
        except ValueError:
            pass

    digest = hashlib.sha256()
    digest.update(f"report-refresh-cache-v{CACHE_VERSION}\n".encode("ascii"))
    digest.update(report_name.encode("utf-8"))
    digest.update(b"\norder\0")
    digest.update("\n".join(order).encode("utf-8"))
    digest.update(b"\n")

    for path in _matching_files(root, default_input_patterns(report_name), excluded=excluded):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\n")

    for dependency in _report_dependencies(report_name):
        dependency_path = report_directory / dependency
        digest.update(f"report:{dependency}\0".encode("utf-8"))
        dependency_digest = file_digest(dependency_path) or "<missing>"
        digest.update(dependency_digest.encode("ascii"))
        digest.update(b"\n")

    return digest.hexdigest()


def default_fingerprints(
    report_names: Sequence[str],
    *,
    root: Path,
    report_directory: Path,
    cache_path: Path,
) -> dict[str, Callable[[], str]]:
    order = tuple(report_names)
    return {
        name: (
            lambda report_name=name: default_report_fingerprint(
                report_name,
                root=root,
                report_directory=report_directory,
                cache_path=cache_path,
                order=order,
            )
        )
        for name in order
    }


def load_cache(path: Path, *, order: Sequence[str]) -> tuple[dict[str, dict[str, str]], bool]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return {}, False
    if not isinstance(payload, dict) or payload.get("version") != CACHE_VERSION:
        return {}, False
    if payload.get("order") != list(order):
        return {}, False
    entries = payload.get("entries")
    if not isinstance(entries, dict):
        return {}, False
    normalized: dict[str, dict[str, str]] = {}
    for name, entry in entries.items():
        if not isinstance(name, str) or not isinstance(entry, dict):
            return {}, False
        input_digest = entry.get("input_digest")
        output_digest = entry.get("output_digest")
        if not isinstance(input_digest, str) or not isinstance(output_digest, str):
            return {}, False
        normalized[name] = {
            "input_digest": input_digest,
            "output_digest": output_digest,
        }
    return normalized, True


def write_cache(
    path: Path,
    *,
    order: Sequence[str],
    entries: Mapping[str, Mapping[str, str]],
) -> None:
    payload: dict[str, Any] = {
        "version": CACHE_VERSION,
        "order": list(order),
        "entries": {
            name: {
                "input_digest": str(entry["input_digest"]),
                "output_digest": str(entry["output_digest"]),
            }
            for name, entry in sorted(entries.items())
        },
    }
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
