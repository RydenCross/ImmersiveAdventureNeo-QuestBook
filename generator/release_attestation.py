from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable, Mapping, Sequence

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PURL_SAFE = re.compile(r"^[A-Za-z0-9._+%-]+$")


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _regular_file(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file() or resolved.is_symlink():
        raise ValueError(f"artifact must be a regular file: {resolved}")
    return resolved


def _component(name: str, version: str) -> dict[str, object]:
    if not name or not version or not _PURL_SAFE.fullmatch(name) or not _PURL_SAFE.fullmatch(version):
        raise ValueError("component name and version must be portable package identifiers")
    return {
        "type": "library",
        "name": name,
        "version": version,
        "purl": f"pkg:pypi/{name}@{version}",
    }


def create_cyclonedx_sbom(
    artifacts: Sequence[Path],
    *,
    version: str,
    components: Iterable[tuple[str, str]] = (),
) -> dict[str, object]:
    if not version or any(ch.isspace() for ch in version):
        raise ValueError("version must be a non-empty portable identifier")
    selected = sorted((_regular_file(path) for path in artifacts), key=lambda p: p.name.casefold())
    if not selected:
        raise ValueError("at least one artifact is required")
    names = [path.name.casefold() for path in selected]
    if len(names) != len(set(names)):
        raise ValueError("artifact filenames must be unique")
    component_rows = sorted((_component(name, component_version) for name, component_version in components), key=lambda row: (str(row["name"]).casefold(), str(row["version"])))
    files = [
        {
            "type": "file",
            "name": path.name,
            "hashes": [{"alg": "SHA-256", "content": _digest(path)}],
            "properties": [{"name": "ftb-quest-maker:size-bytes", "value": str(path.stat().st_size)}],
        }
        for path in selected
    ]
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{hashlib.sha256((version + '|' + '|'.join(names)).encode()).hexdigest()[:32]}",
        "version": 1,
        "metadata": {"component": {"type": "application", "name": "ftb-quest-maker", "version": version}},
        "components": component_rows + files,
    }


def create_slsa_provenance(
    artifacts: Sequence[Path],
    *,
    repository: str,
    revision: str,
    workflow: str,
    builder_id: str = "https://github.com/actions/runner",
) -> dict[str, object]:
    if not repository.startswith("https://github.com/") or repository.endswith("/"):
        raise ValueError("repository must be an HTTPS GitHub repository URL")
    if not revision or any(ch.isspace() for ch in revision):
        raise ValueError("revision must be a non-empty commit or tag identifier")
    if not workflow.startswith(".github/workflows/") or not workflow.endswith((".yml", ".yaml")):
        raise ValueError("workflow must be a checked-in GitHub Actions workflow path")
    selected = sorted((_regular_file(path) for path in artifacts), key=lambda p: p.name.casefold())
    if not selected:
        raise ValueError("at least one artifact is required")
    subjects = [{"name": path.name, "digest": {"sha256": _digest(path)}} for path in selected]
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": subjects,
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://github.com/actions/workflow/v1",
                "externalParameters": {"repository": repository, "ref": revision, "workflow": workflow},
                "resolvedDependencies": [{"uri": repository, "digest": {"gitCommit": revision}}],
            },
            "runDetails": {"builder": {"id": builder_id}, "metadata": {"invocationId": f"{repository}@{revision}:{workflow}"}},
        },
    }


def write_json_document(path: Path, payload: Mapping[str, object]) -> Path:
    target = path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(target)
    return target


def verify_attestation_subjects(document: Mapping[str, object], artifacts: Sequence[Path]) -> tuple[str, ...]:
    expected = {path.name: _digest(_regular_file(path)) for path in artifacts}
    actual: dict[str, str] = {}
    for row in document.get("subject", []):
        if isinstance(row, dict) and isinstance(row.get("name"), str):
            digest = row.get("digest")
            if isinstance(digest, dict) and isinstance(digest.get("sha256"), str):
                actual[row["name"]] = digest["sha256"]
    errors = []
    for name, digest in sorted(expected.items()):
        if not _SHA256.fullmatch(actual.get(name, "")):
            errors.append(f"missing or invalid subject digest: {name}")
        elif actual[name] != digest:
            errors.append(f"subject digest mismatch: {name}")
    errors.extend(f"unexpected subject: {name}" for name in sorted(set(actual) - set(expected)))
    return tuple(errors)
