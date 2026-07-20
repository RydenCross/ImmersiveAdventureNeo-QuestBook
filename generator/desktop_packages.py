from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Callable, Mapping, Sequence
from urllib.parse import quote

from generator.native_distribution import detect_native_platform
from generator.output_writer import atomic_write_text

APPLICATION_ID = "ftb-quest-maker"
APPLICATION_NAME = "FTB Quest Maker"
UPDATE_SCHEMA_VERSION = "1.0"
SUPPORTED_PACKAGE_PLATFORMS = ("windows", "linux")
SUPPORTED_UPDATE_CHANNELS = ("stable", "beta", "nightly")
DEFAULT_NATIVE_DIRECTORY = Path("dist/native")
DEFAULT_PACKAGE_DIRECTORY = Path("dist/packages")
DEFAULT_UPDATE_METADATA_PATH = Path("dist/updates/latest.json")
DEFAULT_WINDOWS_INSTALLER_SCRIPT = Path("packaging/windows/ftb_quest_maker.iss")
DEFAULT_LINUX_APPRUN = Path("packaging/linux/AppRun")
DEFAULT_LINUX_DESKTOP_FILE = Path("packaging/ftb-quest-maker.desktop")
DEFAULT_LINUX_ICON = Path("packaging/linux/ftb-quest-maker.svg")
_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def validate_release_version(version: str) -> str:
    normalized = version.strip()
    if not _VERSION_PATTERN.fullmatch(normalized):
        raise ValueError("version must use semantic version syntax such as 1.2.3 or 1.2.3-beta.1")
    return normalized


def validate_update_channel(channel: str) -> str:
    normalized = channel.strip().casefold()
    if normalized not in SUPPORTED_UPDATE_CHANNELS:
        raise ValueError(
            "channel must be one of: " + ", ".join(SUPPORTED_UPDATE_CHANNELS)
        )
    return normalized


@dataclass(frozen=True, slots=True)
class DesktopPackagePlan:
    platform: str
    version: str
    source_binary: str
    destination_directory: str
    artifact_path: str
    build_directory: str | None
    tool: str
    command: tuple[str, ...]
    recipe_files: tuple[str, ...]
    build_on_target_required: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "platform": self.platform,
            "version": self.version,
            "source_binary": self.source_binary,
            "destination_directory": self.destination_directory,
            "artifact_path": self.artifact_path,
            "build_directory": self.build_directory,
            "tool": self.tool,
            "command": list(self.command),
            "recipe_files": list(self.recipe_files),
            "build_on_target_required": self.build_on_target_required,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                "Desktop package plan: PASS",
                f"Platform: {self.platform}.",
                f"Version: {self.version}.",
                f"Artifact: {self.artifact_path}.",
                f"Tool: {self.tool}.",
                "Command: " + " ".join(self.command),
            )
        )


@dataclass(frozen=True, slots=True)
class DesktopPackageBuild:
    plan: DesktopPackagePlan
    dry_run: bool
    built: bool
    return_code: int
    artifact_sha256: str | None = None
    artifact_bytes: int = 0
    errors: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not self.errors and (self.dry_run or self.built)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "dry_run": self.dry_run,
            "built": self.built,
            "return_code": self.return_code,
            "artifact_sha256": self.artifact_sha256,
            "artifact_bytes": self.artifact_bytes,
            "errors": list(self.errors),
            "plan": self.plan.to_dict(),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Desktop package build: {'PASS' if self.is_clean else 'FAIL'}",
            f"Platform: {self.plan.platform}.",
            f"Dry run: {'yes' if self.dry_run else 'no'}.",
            f"Built: {'yes' if self.built else 'no'}.",
            f"Artifact: {self.plan.artifact_path}.",
            f"Artifact bytes: {self.artifact_bytes}.",
        ]
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


def create_desktop_package_plan(
    platform: str,
    version: str,
    *,
    native_directory: Path = DEFAULT_NATIVE_DIRECTORY,
    destination: Path = DEFAULT_PACKAGE_DIRECTORY,
    tool: str | None = None,
) -> DesktopPackagePlan:
    selected = platform.strip().casefold()
    if selected not in SUPPORTED_PACKAGE_PLATFORMS:
        raise ValueError(
            "platform must be one of: " + ", ".join(SUPPORTED_PACKAGE_PLATFORMS)
        )
    normalized_version = validate_release_version(version)
    native_directory = Path(native_directory)
    destination = Path(destination)
    if selected == "windows":
        source = native_directory / "FTBQuestMaker.exe"
        artifact = destination / f"FTBQuestMaker-{normalized_version}-Setup.exe"
        selected_tool = tool or "iscc"
        output_base = artifact.stem
        command = (
            selected_tool,
            f"/DAppVersion={normalized_version}",
            f"/DSourceBinary={source.as_posix()}",
            f"/DOutputDir={destination.as_posix()}",
            f"/DOutputBaseFilename={output_base}",
            DEFAULT_WINDOWS_INSTALLER_SCRIPT.as_posix(),
        )
        recipes = (DEFAULT_WINDOWS_INSTALLER_SCRIPT.as_posix(),)
        build_directory = None
    else:
        source = native_directory / "FTBQuestMaker"
        artifact = destination / f"FTBQuestMaker-{normalized_version}-x86_64.AppImage"
        appdir = destination / "FTBQuestMaker.AppDir"
        selected_tool = tool or "appimagetool"
        command = (selected_tool, appdir.as_posix(), artifact.as_posix())
        recipes = (
            DEFAULT_LINUX_APPRUN.as_posix(),
            DEFAULT_LINUX_DESKTOP_FILE.as_posix(),
            DEFAULT_LINUX_ICON.as_posix(),
        )
        build_directory = appdir.as_posix()
    return DesktopPackagePlan(
        platform=selected,
        version=normalized_version,
        source_binary=source.as_posix(),
        destination_directory=destination.as_posix(),
        artifact_path=artifact.as_posix(),
        build_directory=build_directory,
        tool=selected_tool,
        command=command,
        recipe_files=recipes,
    )


def _stage_linux_appdir(plan: DesktopPackagePlan) -> None:
    if plan.platform != "linux" or plan.build_directory is None:
        raise ValueError("an AppDir can only be staged for a Linux package plan")
    appdir = Path(plan.build_directory)
    if appdir.exists():
        shutil.rmtree(appdir)
    binary_destination = appdir / "usr/bin/FTBQuestMaker"
    application_destination = appdir / "usr/share/applications/ftb-quest-maker.desktop"
    icon_destination = appdir / "usr/share/icons/hicolor/scalable/apps/ftb-quest-maker.svg"
    binary_destination.parent.mkdir(parents=True, exist_ok=True)
    application_destination.parent.mkdir(parents=True, exist_ok=True)
    icon_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(plan.source_binary, binary_destination)
    shutil.copy2(DEFAULT_LINUX_APPRUN, appdir / "AppRun")
    shutil.copy2(DEFAULT_LINUX_DESKTOP_FILE, appdir / "ftb-quest-maker.desktop")
    shutil.copy2(DEFAULT_LINUX_DESKTOP_FILE, application_destination)
    shutil.copy2(DEFAULT_LINUX_ICON, appdir / "ftb-quest-maker.svg")
    shutil.copy2(DEFAULT_LINUX_ICON, icon_destination)
    (appdir / "AppRun").chmod(0o755)
    binary_destination.chmod(0o755)


def build_desktop_package(
    platform: str,
    version: str,
    *,
    native_directory: Path = DEFAULT_NATIVE_DIRECTORY,
    destination: Path = DEFAULT_PACKAGE_DIRECTORY,
    dry_run: bool = False,
    system_name: str | None = None,
    tool: str | None = None,
    tool_available: bool | None = None,
    runner: Callable[..., subprocess.CompletedProcess[object]] = subprocess.run,
) -> DesktopPackageBuild:
    plan = create_desktop_package_plan(
        platform,
        version,
        native_directory=native_directory,
        destination=destination,
        tool=tool,
    )
    missing_recipes = tuple(name for name in plan.recipe_files if not Path(name).is_file())
    if missing_recipes:
        return DesktopPackageBuild(
            plan,
            dry_run=dry_run,
            built=False,
            return_code=2,
            errors=tuple(f"missing package recipe: {name}" for name in missing_recipes),
        )
    if dry_run:
        return DesktopPackageBuild(plan, dry_run=True, built=False, return_code=0)
    host = detect_native_platform(system_name)
    if host != plan.platform:
        return DesktopPackageBuild(
            plan,
            dry_run=False,
            built=False,
            return_code=2,
            errors=("desktop packages must be built on the target operating system",),
        )
    if not Path(plan.source_binary).is_file():
        return DesktopPackageBuild(
            plan,
            dry_run=False,
            built=False,
            return_code=2,
            errors=(f"missing native application binary: {plan.source_binary}",),
        )
    available = shutil.which(plan.tool) is not None if tool_available is None else tool_available
    if not available:
        return DesktopPackageBuild(
            plan,
            dry_run=False,
            built=False,
            return_code=2,
            errors=(f"required packaging tool is unavailable: {plan.tool}",),
        )
    Path(plan.destination_directory).mkdir(parents=True, exist_ok=True)
    if plan.platform == "linux":
        _stage_linux_appdir(plan)
    completed = runner(plan.command, check=False)
    artifact = Path(plan.artifact_path)
    if completed.returncode != 0:
        return DesktopPackageBuild(
            plan,
            dry_run=False,
            built=False,
            return_code=int(completed.returncode),
            errors=("desktop package build failed",),
        )
    if not artifact.is_file():
        return DesktopPackageBuild(
            plan,
            dry_run=False,
            built=False,
            return_code=2,
            errors=("packaging tool completed without creating the expected artifact",),
        )
    data = artifact.read_bytes()
    return DesktopPackageBuild(
        plan,
        dry_run=False,
        built=True,
        return_code=0,
        artifact_sha256=hashlib.sha256(data).hexdigest(),
        artifact_bytes=len(data),
    )


@dataclass(frozen=True, slots=True)
class UpdateArtifact:
    platform: str
    filename: str
    url: str
    size_bytes: int
    sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "platform": self.platform,
            "filename": self.filename,
            "url": self.url,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class UpdateMetadata:
    version: str
    channel: str
    artifacts: tuple[UpdateArtifact, ...]
    signature_algorithm: str | None = None
    signature_key_id: str | None = None
    signature_value: str | None = None

    @property
    def signed(self) -> bool:
        return self.signature_value is not None

    def unsigned_dict(self) -> dict[str, object]:
        return {
            "schema_version": UPDATE_SCHEMA_VERSION,
            "application_id": APPLICATION_ID,
            "application_name": APPLICATION_NAME,
            "version": self.version,
            "channel": self.channel,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
        }

    def to_dict(self) -> dict[str, object]:
        payload = self.unsigned_dict()
        if self.signed:
            payload["signature"] = {
                "algorithm": self.signature_algorithm,
                "key_id": self.signature_key_id,
                "value": self.signature_value,
            }
        return payload

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True, slots=True)
class UpdateMetadataBuild:
    destination: str
    metadata_sha256: str
    version: str
    channel: str
    artifact_count: int
    signed: bool
    errors: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "destination": self.destination,
            "metadata_sha256": self.metadata_sha256,
            "version": self.version,
            "channel": self.channel,
            "artifact_count": self.artifact_count,
            "signed": self.signed,
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Application update metadata: {'PASS' if self.is_clean else 'FAIL'}",
            f"Version: {self.version}.",
            f"Channel: {self.channel}.",
            f"Artifacts: {self.artifact_count}.",
            f"Signed: {'yes' if self.signed else 'no'}.",
            f"Destination: {self.destination}.",
            f"Metadata SHA-256: {self.metadata_sha256}.",
        ]
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


def _canonical_json(payload: Mapping[str, object]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _artifact_platform_from_path(path: Path) -> str:
    name = path.name.casefold()
    if name.endswith(".exe"):
        return "windows"
    if name.endswith(".appimage"):
        return "linux"
    raise ValueError(f"cannot infer update platform from artifact filename: {path.name}")


def parse_artifact_specs(values: Sequence[str]) -> dict[str, Path]:
    artifacts: dict[str, Path] = {}
    for value in values:
        if "=" in value:
            platform, raw_path = value.split("=", 1)
            selected = platform.strip().casefold()
            path = Path(raw_path.strip())
        else:
            path = Path(value.strip())
            selected = _artifact_platform_from_path(path)
        if selected not in SUPPORTED_PACKAGE_PLATFORMS:
            raise ValueError(f"unsupported update artifact platform: {selected}")
        if selected in artifacts:
            raise ValueError(f"duplicate update artifact platform: {selected}")
        artifacts[selected] = path
    if not artifacts:
        raise ValueError("at least one update artifact is required")
    return artifacts


def create_update_metadata(
    version: str,
    channel: str,
    artifacts: Mapping[str, Path],
    *,
    base_url: str = "",
    signing_key: bytes | None = None,
    key_id: str = "local",
) -> UpdateMetadata:
    normalized_version = validate_release_version(version)
    normalized_channel = validate_update_channel(channel)
    if normalized_channel == "stable" and "-" in normalized_version:
        raise ValueError("stable update metadata cannot publish a prerelease version")
    records: list[UpdateArtifact] = []
    for platform, path_value in sorted(artifacts.items()):
        selected = platform.strip().casefold()
        if selected not in SUPPORTED_PACKAGE_PLATFORMS:
            raise ValueError(f"unsupported update artifact platform: {selected}")
        path = Path(path_value)
        if not path.is_file():
            raise ValueError(f"missing update artifact: {path}")
        inferred = _artifact_platform_from_path(path)
        if inferred != selected:
            raise ValueError(
                f"artifact extension does not match platform {selected}: {path.name}"
            )
        data = path.read_bytes()
        prefix = base_url.rstrip("/")
        url = f"{prefix}/{quote(path.name)}" if prefix else quote(path.name)
        records.append(
            UpdateArtifact(
                platform=selected,
                filename=path.name,
                url=url,
                size_bytes=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
            )
        )
    unsigned = UpdateMetadata(normalized_version, normalized_channel, tuple(records))
    if signing_key is None:
        return unsigned
    if not signing_key:
        raise ValueError("signing key cannot be empty")
    normalized_key_id = key_id.strip()
    if not normalized_key_id:
        raise ValueError("key_id cannot be empty")
    signature = hmac.new(
        signing_key,
        _canonical_json(unsigned.unsigned_dict()),
        hashlib.sha256,
    ).hexdigest()
    return UpdateMetadata(
        normalized_version,
        normalized_channel,
        tuple(records),
        signature_algorithm="hmac-sha256",
        signature_key_id=normalized_key_id,
        signature_value=signature,
    )


def write_update_metadata(metadata: UpdateMetadata, destination: Path) -> UpdateMetadataBuild:
    rendered = metadata.format_json().rstrip() + "\n"
    atomic_write_text(destination, rendered)
    return UpdateMetadataBuild(
        destination=Path(destination).as_posix(),
        metadata_sha256=hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        version=metadata.version,
        channel=metadata.channel,
        artifact_count=len(metadata.artifacts),
        signed=metadata.signed,
    )


@dataclass(frozen=True, slots=True)
class UpdateMetadataVerification:
    metadata_path: str
    version: str | None
    channel: str | None
    artifact_count: int
    metadata_signed: bool
    signature_valid: bool | None
    verified_artifacts: tuple[str, ...]
    missing_artifacts: tuple[str, ...]
    changed_artifacts: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.missing_artifacts, self.changed_artifacts, self.errors))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "metadata_path": self.metadata_path,
            "version": self.version,
            "channel": self.channel,
            "artifact_count": self.artifact_count,
            "metadata_signed": self.metadata_signed,
            "signature_valid": self.signature_valid,
            "verified_artifacts": list(self.verified_artifacts),
            "missing_artifacts": list(self.missing_artifacts),
            "changed_artifacts": list(self.changed_artifacts),
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Application update verification: {'PASS' if self.is_clean else 'FAIL'}",
            f"Version: {self.version or '<unknown>'}.",
            f"Channel: {self.channel or '<unknown>'}.",
            f"Artifacts: {self.artifact_count}.",
            f"Signed metadata: {'yes' if self.metadata_signed else 'no'}.",
            f"Verified artifacts: {len(self.verified_artifacts)}.",
            f"Missing artifacts: {len(self.missing_artifacts)}.",
            f"Changed artifacts: {len(self.changed_artifacts)}.",
        ]
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


def verify_update_metadata(
    metadata_path: Path,
    *,
    artifact_directory: Path | None = None,
    signing_key: bytes | None = None,
) -> UpdateMetadataVerification:
    errors: list[str] = []
    missing: list[str] = []
    changed: list[str] = []
    verified: list[str] = []
    version: str | None = None
    channel: str | None = None
    artifact_count = 0
    metadata_signed = False
    signature_valid: bool | None = None
    try:
        payload = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("update metadata root must be an object")
        if payload.get("schema_version") != UPDATE_SCHEMA_VERSION:
            errors.append("unsupported update metadata schema")
        if payload.get("application_id") != APPLICATION_ID:
            errors.append("unexpected application identifier")
        version = validate_release_version(str(payload.get("version", "")))
        channel = validate_update_channel(str(payload.get("channel", "")))
        raw_artifacts = payload.get("artifacts")
        if not isinstance(raw_artifacts, list) or not raw_artifacts:
            errors.append("update metadata must contain at least one artifact")
            raw_artifacts = []
        artifact_count = len(raw_artifacts)
        platforms: set[str] = set()
        filenames: set[str] = set()
        normalized_artifacts: list[dict[str, object]] = []
        for raw in raw_artifacts:
            if not isinstance(raw, dict):
                errors.append("update artifact records must be objects")
                continue
            platform = str(raw.get("platform", "")).casefold()
            filename = str(raw.get("filename", ""))
            sha256 = str(raw.get("sha256", ""))
            size = raw.get("size_bytes")
            url = str(raw.get("url", ""))
            if platform not in SUPPORTED_PACKAGE_PLATFORMS:
                errors.append(f"unsupported artifact platform: {platform}")
            if platform in platforms:
                errors.append(f"duplicate artifact platform: {platform}")
            platforms.add(platform)
            if not filename or Path(filename).name != filename:
                errors.append(f"unsafe artifact filename: {filename}")
            if filename in filenames:
                errors.append(f"duplicate artifact filename: {filename}")
            filenames.add(filename)
            if not _SHA256_PATTERN.fullmatch(sha256):
                errors.append(f"invalid artifact SHA-256: {filename}")
            if not isinstance(size, int) or isinstance(size, bool) or size < 1:
                errors.append(f"invalid artifact size: {filename}")
            normalized_artifacts.append(
                {
                    "platform": platform,
                    "filename": filename,
                    "url": url,
                    "size_bytes": size,
                    "sha256": sha256,
                }
            )
            if artifact_directory is not None and filename:
                artifact = Path(artifact_directory) / filename
                if not artifact.is_file():
                    missing.append(filename)
                else:
                    data = artifact.read_bytes()
                    if len(data) != size or hashlib.sha256(data).hexdigest() != sha256:
                        changed.append(filename)
                    else:
                        verified.append(filename)
        signature = payload.get("signature")
        metadata_signed = isinstance(signature, dict)
        unsigned_payload = {
            "schema_version": payload.get("schema_version"),
            "application_id": payload.get("application_id"),
            "application_name": payload.get("application_name"),
            "version": payload.get("version"),
            "channel": payload.get("channel"),
            "artifacts": normalized_artifacts,
        }
        if metadata_signed:
            algorithm = str(signature.get("algorithm", ""))
            value = str(signature.get("value", ""))
            if algorithm != "hmac-sha256" or not _SHA256_PATTERN.fullmatch(value):
                errors.append("invalid update metadata signature")
                signature_valid = False
            elif signing_key is None:
                errors.append("a signing key is required to verify signed update metadata")
                signature_valid = False
            else:
                expected = hmac.new(
                    signing_key,
                    _canonical_json(unsigned_payload),
                    hashlib.sha256,
                ).hexdigest()
                signature_valid = hmac.compare_digest(expected, value)
                if not signature_valid:
                    errors.append("update metadata signature mismatch")
        elif signing_key is not None:
            signature_valid = False
            errors.append("update metadata is unsigned")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
    return UpdateMetadataVerification(
        metadata_path=Path(metadata_path).as_posix(),
        version=version,
        channel=channel,
        artifact_count=artifact_count,
        metadata_signed=metadata_signed,
        signature_valid=signature_valid,
        verified_artifacts=tuple(sorted(verified)),
        missing_artifacts=tuple(sorted(missing)),
        changed_artifacts=tuple(sorted(changed)),
        errors=tuple(errors),
    )
