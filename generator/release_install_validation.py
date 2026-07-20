from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from generator.desktop_packages import verify_update_metadata

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class ReleaseInstallValidation:
    windows_artifact: str | None
    linux_artifact: str | None
    verified_files: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "windows_artifact": self.windows_artifact,
            "linux_artifact": self.linux_artifact,
            "verified_files": list(self.verified_files),
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_checksums(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or not _SHA256.fullmatch(parts[0]):
            raise ValueError(f"invalid checksum line {number}")
        name = parts[1].lstrip(" *").strip()
        if not name or Path(name).name != name or name in result:
            raise ValueError(f"invalid or duplicate checksum filename on line {number}")
        result[name] = parts[0]
    return result



def _artifact_digest_map(paths: list[Path]) -> dict[str, str]:
    return {path.name: _sha256(path) for path in paths}


def _canonical_sha256(value: object) -> str | None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        return None
    return value


def _validate_sbom(path: Path, installers: list[Path], *, expected_version: str | None = None) -> tuple[str, ...]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return (f"invalid CycloneDX SBOM: {exc}",)
    if not isinstance(payload, dict):
        return ("CycloneDX SBOM root must be an object",)
    if payload.get("bomFormat") != "CycloneDX":
        errors.append("SBOM bomFormat must be CycloneDX")
    if payload.get("specVersion") != "1.5":
        errors.append("SBOM specVersion must be 1.5")
    if payload.get("version") != 1:
        errors.append("SBOM document version must be 1")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        errors.append("SBOM metadata must be an object")
    application = metadata.get("component")
    if not isinstance(application, dict):
        application = {}
        errors.append("SBOM metadata component must be an object")
    if application.get("type") != "application":
        errors.append("SBOM metadata component type must be application")
    if application.get("name") != "ftb-quest-maker":
        errors.append("SBOM application name must be ftb-quest-maker")
    if expected_version is not None and application.get("version") != expected_version:
        errors.append("SBOM application version does not match expected release version")
    components = payload.get("components")
    if not isinstance(components, list):
        return tuple(errors + ["SBOM components must be an array"])

    expected = _artifact_digest_map(installers)
    expected_sizes = {path.name: path.stat().st_size for path in installers}
    if expected_version is not None:
        serial_material = expected_version + "|" + "|".join(sorted(name.casefold() for name in expected))
        expected_serial = f"urn:uuid:{hashlib.sha256(serial_material.encode()).hexdigest()[:32]}"
        if payload.get("serialNumber") != expected_serial:
            errors.append("SBOM serialNumber does not match release version and installer set")
    actual: dict[str, str] = {}
    seen: set[str] = set()
    for row in components:
        if not isinstance(row, dict):
            errors.append("SBOM component entries must be objects")
            continue
        if row.get("type") != "file":
            continue
        name = row.get("name")
        if not isinstance(name, str) or not name or Path(name).name != name:
            errors.append("SBOM file components must have safe filenames")
            continue
        if name in seen:
            errors.append(f"SBOM contains duplicate file component {name}")
            continue
        seen.add(name)
        hashes = row.get("hashes")
        if not isinstance(hashes, list):
            errors.append(f"SBOM hashes must be an array for {name}")
            continue
        sha_values: list[str] = []
        for digest in hashes:
            if not isinstance(digest, dict):
                errors.append(f"SBOM hash entries must be objects for {name}")
                continue
            if digest.get("alg") == "SHA-256":
                value = _canonical_sha256(digest.get("content"))
                if value is None:
                    errors.append(f"SBOM contains non-canonical SHA-256 for {name}")
                else:
                    sha_values.append(value)
        if len(sha_values) != 1:
            errors.append(f"SBOM must contain exactly one SHA-256 for {name}")
        else:
            actual[name] = sha_values[0]
        properties = row.get("properties")
        if not isinstance(properties, list):
            errors.append(f"SBOM properties must be an array for {name}")
        else:
            size_values = [
                prop.get("value") for prop in properties
                if isinstance(prop, dict) and prop.get("name") == "ftb-quest-maker:size-bytes"
            ]
            if len(size_values) != 1 or size_values[0] != str(expected_sizes.get(name, "")):
                errors.append(f"SBOM size property does not match staged artifact for {name}")
    for name, digest in sorted(expected.items()):
        if actual.get(name) != digest:
            errors.append(f"SBOM does not bind SHA-256 for {name}")
    for name in sorted(set(actual) - set(expected)):
        errors.append(f"SBOM references unexpected file component {name}")
    return tuple(errors)


def _validate_provenance(
    path: Path,
    installers: list[Path],
    *,
    revision: str | None,
    repository: str | None,
    workflow: str,
) -> tuple[str, ...]:
    errors: list[str] = []
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(lines) != 1:
            raise ValueError("expected exactly one JSON statement")
        payload = json.loads(lines[0])
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return (f"invalid provenance statement: {exc}",)
    if not isinstance(payload, dict):
        return ("provenance statement root must be an object",)
    if payload.get("_type") != "https://in-toto.io/Statement/v1":
        errors.append("provenance statement has invalid in-toto type")
    if payload.get("predicateType") != "https://slsa.dev/provenance/v1":
        errors.append("provenance statement has invalid SLSA predicate type")

    subjects = payload.get("subject")
    if not isinstance(subjects, list):
        subjects = []
        errors.append("provenance subject must be an array")
    expected = _artifact_digest_map(installers)
    actual: dict[str, str] = {}
    seen: set[str] = set()
    for row in subjects:
        if not isinstance(row, dict):
            errors.append("provenance subject entries must be objects")
            continue
        name = row.get("name")
        if not isinstance(name, str) or not name or Path(name).name != name:
            errors.append("provenance subjects must have safe filenames")
            continue
        if name in seen:
            errors.append(f"provenance contains duplicate subject {name}")
            continue
        seen.add(name)
        digest = row.get("digest")
        if not isinstance(digest, dict):
            errors.append(f"provenance digest must be an object for {name}")
            continue
        if set(digest) != {"sha256"}:
            errors.append(f"provenance digest must contain only sha256 for {name}")
        value = _canonical_sha256(digest.get("sha256"))
        if value is None:
            errors.append(f"provenance contains non-canonical SHA-256 for {name}")
        else:
            actual[name] = value
    for name, digest in sorted(expected.items()):
        if actual.get(name) != digest:
            errors.append(f"provenance does not bind SHA-256 for {name}")
    for name in sorted(set(actual) - set(expected)):
        errors.append(f"provenance references unexpected subject {name}")

    predicate = payload.get("predicate")
    if not isinstance(predicate, dict):
        return tuple(errors + ["provenance predicate must be an object"])
    build = predicate.get("buildDefinition")
    if not isinstance(build, dict):
        return tuple(errors + ["provenance buildDefinition must be an object"])
    params = build.get("externalParameters")
    if not isinstance(params, dict):
        params = {}
        errors.append("provenance externalParameters must be an object")
    run_details = predicate.get("runDetails")
    if not isinstance(run_details, dict):
        run_details = {}
        errors.append("provenance runDetails must be an object")
    builder = run_details.get("builder")
    if not isinstance(builder, dict):
        builder = {}
        errors.append("provenance builder must be an object")
    metadata = run_details.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        errors.append("provenance metadata must be an object")

    if build.get("buildType") != "https://github.com/actions/workflow/v1":
        errors.append("provenance build type must identify GitHub Actions workflow v1")
    if builder.get("id") != "https://github.com/actions/runner":
        errors.append("provenance builder identity does not match GitHub Actions runner")
    if revision is not None and params.get("ref") != revision:
        errors.append("provenance source revision does not match verified release source")
    if repository is not None and params.get("repository") != repository:
        errors.append("provenance repository does not match expected repository")
    if params.get("workflow") != workflow:
        errors.append("provenance workflow does not match release workflow")

    deps = build.get("resolvedDependencies")
    if not isinstance(deps, list):
        deps = []
        errors.append("provenance resolvedDependencies must be an array")
    if revision is not None and repository is not None:
        valid_deps = [
            row for row in deps
            if isinstance(row, dict)
            and row.get("uri") == repository
            and isinstance(row.get("digest"), dict)
            and row["digest"].get("gitCommit") == revision
        ]
        if len(deps) != 1 or len(valid_deps) != 1:
            errors.append("provenance must contain exactly one repository-bound resolved dependency for verified release source")
        expected_invocation = f"{repository}@{revision}:{workflow}"
        if metadata.get("invocationId") != expected_invocation:
            errors.append("provenance invocation identity does not match repository, revision, and workflow")
    return tuple(errors)

def validate_release_installers(
    assets: Path,
    checksums: Path,
    update_metadata: Path,
    *,
    minimum_bytes: int = 4096,
    expected_revision: str | None = None,
    expected_repository: str | None = None,
    expected_workflow: str = ".github/workflows/publish-release.yml",
    expected_version: str | None = None,
) -> ReleaseInstallValidation:
    assets = assets.resolve()
    checksums = checksums.resolve()
    update_metadata = update_metadata.resolve()
    errors: list[str] = []

    expected_checksums = assets / "SHA256SUMS"
    expected_update = assets / "update.json"
    if checksums != expected_checksums:
        errors.append("checksum manifest must be the release-assets/SHA256SUMS file")
    if update_metadata != expected_update:
        errors.append("update metadata must be the release-assets/update.json file")
    verified: list[str] = []
    all_entries = sorted(assets.rglob("*"))
    regular_files: list[Path] = []
    for path in all_entries:
        try:
            mode = path.lstat().st_mode
        except OSError as exc:
            errors.append(f"cannot inspect staged asset {path.name}: {exc}")
            continue
        if stat.S_ISLNK(mode):
            errors.append(f"symbolic links are not allowed in release assets: {path.name}")
        elif stat.S_ISREG(mode):
            regular_files.append(path)
            if path.parent != assets:
                errors.append(f"release assets must be stored directly in the asset root: {path.relative_to(assets)}")
        elif not stat.S_ISDIR(mode):
            errors.append(f"non-regular release asset is not allowed: {path.name}")

    basenames = [path.name for path in regular_files]
    duplicate_names = sorted({name for name in basenames if basenames.count(name) > 1})
    for name in duplicate_names:
        errors.append(f"duplicate release asset basename: {name}")

    windows = sorted(path for path in regular_files if path.suffix.casefold() == ".exe")
    linux = sorted(path for path in regular_files if path.suffix == ".AppImage")
    sboms = sorted(path for path in regular_files if path.name.endswith(".cdx.json"))
    provenance = sorted(path for path in regular_files if path.name.endswith(".intoto.jsonl"))
    updates = sorted(path for path in regular_files if path.name == "update.json")
    checksum_files = sorted(path for path in regular_files if path.name == "SHA256SUMS")

    if len(windows) != 1:
        errors.append(f"expected exactly one Windows installer, found {len(windows)}")
    if len(linux) != 1:
        errors.append(f"expected exactly one Linux AppImage, found {len(linux)}")
    if len(sboms) != 1:
        errors.append(f"expected exactly one CycloneDX SBOM, found {len(sboms)}")
    if len(provenance) != 1:
        errors.append(f"expected exactly one provenance statement, found {len(provenance)}")
    if len(updates) != 1:
        errors.append(f"expected exactly one update.json, found {len(updates)}")
    if len(checksum_files) != 1:
        errors.append(f"expected exactly one SHA256SUMS, found {len(checksum_files)}")

    allowed = {
        *(path.name for path in windows),
        *(path.name for path in linux),
        *(path.name for path in sboms),
        *(path.name for path in provenance),
        "update.json",
        "SHA256SUMS",
    }
    for path in regular_files:
        if path.name not in allowed:
            errors.append(f"unexpected release asset: {path.name}")

    try:
        manifest = _read_checksums(checksums)
    except (OSError, UnicodeError, ValueError) as exc:
        manifest = {}
        errors.append(f"invalid checksum manifest: {exc}")

    expected_manifest_names = {path.name for path in regular_files if path.name != "SHA256SUMS"}
    manifest_names = set(manifest)
    for name in sorted(expected_manifest_names - manifest_names):
        errors.append(f"checksum manifest is missing staged asset {name}")
    for name in sorted(manifest_names - expected_manifest_names):
        errors.append(f"checksum manifest references unexpected asset {name}")

    for path in regular_files:
        if path.name == "SHA256SUMS":
            continue
        try:
            digest = _sha256(path)
        except OSError as exc:
            errors.append(f"cannot hash {path.name}: {exc}")
            continue
        expected = manifest.get(path.name)
        if expected is None:
            errors.append(f"checksum manifest is missing {path.name}")
        elif expected != digest:
            errors.append(f"checksum mismatch for {path.name}")
        else:
            verified.append(path.name)

    selected = windows[:1] + linux[:1]
    if len(sboms) == 1 and len(selected) == 2:
        errors.extend(_validate_sbom(sboms[0], selected, expected_version=expected_version))
    if len(provenance) == 1 and len(selected) == 2:
        errors.extend(_validate_provenance(
            provenance[0], selected, revision=expected_revision,
            repository=expected_repository, workflow=expected_workflow,
        ))
    for path in selected:
        try:
            size = path.stat().st_size
            header = path.read_bytes()[:4]
        except OSError as exc:
            errors.append(f"cannot read {path.name}: {exc}")
            continue
        if size < minimum_bytes:
            errors.append(f"artifact is unexpectedly small: {path.name} ({size} bytes)")
        if path.suffix.casefold() == ".exe" and not header.startswith(b"MZ"):
            errors.append(f"Windows installer lacks PE MZ signature: {path.name}")
        if path.suffix == ".AppImage":
            if header != b"\x7fELF":
                errors.append(f"AppImage lacks ELF signature: {path.name}")
            if os.name != "nt" and not os.access(path, os.X_OK):
                errors.append(f"AppImage is not executable: {path.name}")

    update_verification = verify_update_metadata(
        update_metadata, artifact_directory=assets
    )
    if expected_version is not None and update_verification.version != expected_version:
        errors.append("update metadata version does not match expected release version")
    errors.extend(f"invalid update metadata: {error}" for error in update_verification.errors)
    errors.extend(
        f"update metadata is missing artifact {name}"
        for name in update_verification.missing_artifacts
    )
    errors.extend(
        f"update metadata does not bind filename, size, and SHA-256 for {name}"
        for name in update_verification.changed_artifacts
    )
    selected_names = {path.name for path in selected}
    verified_update_names = set(update_verification.verified_artifacts)
    if update_verification.artifact_count != len(selected_names):
        errors.append(
            f"update metadata must contain exactly {len(selected_names)} installer records"
        )
    for name in sorted(selected_names - verified_update_names):
        errors.append(f"update metadata does not bind installer {name}")
    for name in sorted(verified_update_names - selected_names):
        errors.append(f"update metadata references unexpected installer {name}")

    return ReleaseInstallValidation(
        windows[0].name if len(windows) == 1 else None,
        linux[0].name if len(linux) == 1 else None,
        tuple(sorted(verified)),
        tuple(sorted(set(errors))),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate release installers before publication.")
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--checksums", type=Path, required=True)
    parser.add_argument("--update", type=Path, required=True)
    parser.add_argument("--minimum-bytes", type=int, default=4096)
    parser.add_argument("--expected-revision")
    parser.add_argument("--expected-repository")
    parser.add_argument("--expected-workflow", default=".github/workflows/publish-release.yml")
    parser.add_argument("--expected-version")
    args = parser.parse_args(argv)
    result = validate_release_installers(
        args.assets, args.checksums, args.update, minimum_bytes=args.minimum_bytes,
        expected_revision=args.expected_revision, expected_repository=args.expected_repository,
        expected_workflow=args.expected_workflow, expected_version=args.expected_version
    )
    print(result.format_json())
    return 0 if result.is_clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
