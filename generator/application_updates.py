from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import tempfile
from typing import BinaryIO, Callable
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, url2pathname, urlopen

from generator.desktop_packages import (
    SUPPORTED_PACKAGE_PLATFORMS,
    SUPPORTED_UPDATE_CHANNELS,
    validate_release_version,
    validate_update_channel,
    verify_update_metadata,
)
from generator.native_distribution import detect_native_platform
from generator.output_writer import atomic_write_text

DEFAULT_UPDATE_STAGE_DIRECTORY = Path.home() / ".ftb-quest-maker" / "updates"
DEFAULT_METADATA_LIMIT_BYTES = 1024 * 1024
DEFAULT_ARTIFACT_LIMIT_BYTES = 2 * 1024 * 1024 * 1024
DEFAULT_UPDATE_TIMEOUT_SECONDS = 15.0
UPDATE_STAGE_SCHEMA_VERSION = "1.0"
USER_AGENT = "FTB-Quest-Maker-Updater/1.0"


def _noop() -> None:
    pass


@dataclass(frozen=True, slots=True)
class SemanticVersion:
    major: int
    minor: int
    patch: int
    prerelease: tuple[int | str, ...]

    @classmethod
    def parse(cls, value: str) -> SemanticVersion:
        normalized = validate_release_version(value)
        without_build = normalized.split("+", 1)[0]
        core, separator, raw_prerelease = without_build.partition("-")
        major, minor, patch = (int(item) for item in core.split("."))
        prerelease: list[int | str] = []
        if separator:
            for item in raw_prerelease.split("."):
                prerelease.append(int(item) if item.isdigit() else item.casefold())
        return cls(major, minor, patch, tuple(prerelease))

    def compare(self, other: SemanticVersion) -> int:
        own_core = (self.major, self.minor, self.patch)
        other_core = (other.major, other.minor, other.patch)
        if own_core != other_core:
            return 1 if own_core > other_core else -1
        if not self.prerelease and not other.prerelease:
            return 0
        if not self.prerelease:
            return 1
        if not other.prerelease:
            return -1
        for own, candidate in zip(self.prerelease, other.prerelease):
            if own == candidate:
                continue
            if isinstance(own, int) and isinstance(candidate, str):
                return -1
            if isinstance(own, str) and isinstance(candidate, int):
                return 1
            return 1 if own > candidate else -1
        if len(self.prerelease) == len(other.prerelease):
            return 0
        return 1 if len(self.prerelease) > len(other.prerelease) else -1


def compare_release_versions(left: str, right: str) -> int:
    return SemanticVersion.parse(left).compare(SemanticVersion.parse(right))


@dataclass(frozen=True, slots=True)
class UpdateCandidate:
    platform: str
    filename: str
    source: str
    size_bytes: int
    sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "platform": self.platform,
            "filename": self.filename,
            "source": self.source,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class ApplicationUpdateCheck:
    metadata_source: str
    current_version: str
    latest_version: str | None
    requested_channel: str
    published_channel: str | None
    platform: str
    update_available: bool
    metadata_signed: bool
    signature_valid: bool | None
    candidate: UpdateCandidate | None
    errors: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "metadata_source": self.metadata_source,
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "requested_channel": self.requested_channel,
            "published_channel": self.published_channel,
            "platform": self.platform,
            "update_available": self.update_available,
            "metadata_signed": self.metadata_signed,
            "signature_valid": self.signature_valid,
            "candidate": self.candidate.to_dict() if self.candidate else None,
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Application update check: {'PASS' if self.is_clean else 'FAIL'}",
            f"Current version: {self.current_version}.",
            f"Latest version: {self.latest_version or '<unknown>'}.",
            f"Channel: {self.requested_channel}.",
            f"Platform: {self.platform}.",
            f"Update available: {'yes' if self.update_available else 'no'}.",
            f"Signed metadata: {'yes' if self.metadata_signed else 'no'}.",
        ]
        if self.candidate:
            lines.append(f"Artifact: {self.candidate.filename}.")
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class ApplicationUpdateStage:
    check: ApplicationUpdateCheck
    destination_directory: str
    staged_path: str | None
    manifest_path: str | None
    downloaded: bool
    reused: bool
    artifact_bytes: int
    artifact_sha256: str | None
    errors: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return self.check.is_clean and not self.errors

    @property
    def staged(self) -> bool:
        return self.staged_path is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "destination_directory": self.destination_directory,
            "staged_path": self.staged_path,
            "manifest_path": self.manifest_path,
            "downloaded": self.downloaded,
            "reused": self.reused,
            "staged": self.staged,
            "artifact_bytes": self.artifact_bytes,
            "artifact_sha256": self.artifact_sha256,
            "errors": list(self.errors),
            "check": self.check.to_dict(),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Application update staging: {'PASS' if self.is_clean else 'FAIL'}",
            f"Update available: {'yes' if self.check.update_available else 'no'}.",
            f"Staged: {'yes' if self.staged else 'no'}.",
            f"Downloaded: {'yes' if self.downloaded else 'no'}.",
            f"Reused: {'yes' if self.reused else 'no'}.",
            f"Destination: {self.staged_path or '<none>'}.",
        ]
        lines.extend(f"Error: {error}" for error in (*self.check.errors, *self.errors))
        return "\n".join(lines)


def _validate_https_url(value: str, *, label: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme.casefold() != "https":
        raise ValueError(f"{label} must use HTTPS")
    if not parsed.netloc or parsed.username or parsed.password:
        raise ValueError(f"{label} must use a public HTTPS host without credentials")
    if parsed.fragment:
        raise ValueError(f"{label} must not contain a URL fragment")
    return value


def _read_stream_bounded(stream: BinaryIO, limit: int) -> bytes:
    if limit < 1:
        raise ValueError("download limit must be positive")
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = stream.read(min(1024 * 1024, limit - total + 1))
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise ValueError(f"download exceeded the {limit}-byte limit")
        chunks.append(chunk)
    return b"".join(chunks)


def _open_remote_bytes(
    url: str,
    *,
    limit: int,
    timeout: float,
    opener: Callable[..., object],
    accept: str,
) -> tuple[bytes, str]:
    _validate_https_url(url, label="update source")
    request = Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
    response = opener(request, timeout=timeout)
    try:
        final_url = str(getattr(response, "geturl", lambda: url)())
        _validate_https_url(final_url, label="redirected update source")
        data = _read_stream_bounded(response, limit)  # type: ignore[arg-type]
    finally:
        close = getattr(response, "close", None)
        if callable(close):
            close()
    return data, final_url


def _looks_like_windows_path(value: str) -> bool:
    return len(value) >= 3 and value[1] == ":" and value[2] in ("/", "\\")


def _read_metadata_source(
    source: str | Path,
    *,
    max_bytes: int,
    timeout: float,
    opener: Callable[..., object],
) -> tuple[bytes, str, bool]:
    raw = str(source)
    parsed = urlparse(raw)
    if parsed.scheme and not _looks_like_windows_path(raw):
        data, resolved = _open_remote_bytes(
            raw,
            limit=max_bytes,
            timeout=timeout,
            opener=opener,
            accept="application/json",
        )
        return data, resolved, True
    path = Path(source).expanduser().absolute()
    if not path.is_file():
        raise ValueError(f"update metadata does not exist: {path}")
    if path.stat().st_size > max_bytes:
        raise ValueError(f"update metadata exceeded the {max_bytes}-byte limit")
    return path.read_bytes(), path.as_uri(), False


def _accepted_channels(requested: str) -> tuple[str, ...]:
    if requested == "stable":
        return ("stable",)
    if requested == "beta":
        return ("stable", "beta")
    return SUPPORTED_UPDATE_CHANNELS


def _validate_portable_artifact_filename(filename: str) -> str:
    if (
        not filename
        or filename in (".", "..")
        or PurePosixPath(filename).name != filename
        or PureWindowsPath(filename).name != filename
    ):
        raise ValueError(f"unsafe update artifact filename: {filename}")
    return filename


def _resolve_artifact_source(
    metadata_source: str,
    artifact_url: str,
    filename: str,
    *,
    remote_metadata: bool,
) -> str:
    filename = _validate_portable_artifact_filename(filename)
    resolved = urljoin(metadata_source, artifact_url)
    parsed = urlparse(resolved)
    if remote_metadata:
        _validate_https_url(resolved, label="update artifact URL")
    elif parsed.scheme.casefold() not in ("file", "https"):
        raise ValueError("local update metadata may reference only file or HTTPS artifacts")
    elif parsed.scheme.casefold() == "https":
        _validate_https_url(resolved, label="update artifact URL")
    elif parsed.netloc not in ("", "localhost"):
        raise ValueError("file update artifact URL must not reference a remote host")
    if Path(unquote(parsed.path)).name != filename:
        raise ValueError("update artifact URL filename does not match metadata")
    return resolved


def check_for_application_update(
    source: str | Path,
    current_version: str,
    *,
    channel: str = "stable",
    platform: str = "auto",
    signing_key: bytes | None = None,
    require_signature: bool = False,
    max_metadata_bytes: int = DEFAULT_METADATA_LIMIT_BYTES,
    timeout: float = DEFAULT_UPDATE_TIMEOUT_SECONDS,
    opener: Callable[..., object] = urlopen,
) -> ApplicationUpdateCheck:
    errors: list[str] = []
    latest_version: str | None = None
    published_channel: str | None = None
    metadata_signed = False
    signature_valid: bool | None = None
    candidate: UpdateCandidate | None = None
    selected_platform = platform.strip().casefold()
    metadata_source = str(source)
    try:
        normalized_current = validate_release_version(current_version)
        requested_channel = validate_update_channel(channel)
        if selected_platform == "auto":
            selected_platform = detect_native_platform()
        if selected_platform not in SUPPORTED_PACKAGE_PLATFORMS:
            raise ValueError("update checks support only Windows and Linux packages")
        metadata_bytes, metadata_source, remote = _read_metadata_source(
            source,
            max_bytes=max_metadata_bytes,
            timeout=timeout,
            opener=opener,
        )
        with tempfile.TemporaryDirectory(prefix="ftbq-update-check-") as temporary:
            metadata_path = Path(temporary) / "latest.json"
            metadata_path.write_bytes(metadata_bytes)
            verification = verify_update_metadata(metadata_path, signing_key=signing_key)
        metadata_signed = verification.metadata_signed
        signature_valid = verification.signature_valid
        errors.extend(verification.errors)
        if require_signature and not metadata_signed:
            errors.append("signed update metadata is required")
        payload = json.loads(metadata_bytes.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("update metadata root must be an object")
        latest_version = validate_release_version(str(payload.get("version", "")))
        published_channel = validate_update_channel(str(payload.get("channel", "")))
        if published_channel not in _accepted_channels(requested_channel):
            errors.append(f"{requested_channel} clients do not accept {published_channel} updates")
        raw_artifacts = payload.get("artifacts")
        if not isinstance(raw_artifacts, list):
            raise ValueError("update metadata artifacts must be a list")
        matches = [
            item
            for item in raw_artifacts
            if isinstance(item, dict)
            and str(item.get("platform", "")).casefold() == selected_platform
        ]
        if len(matches) != 1:
            errors.append(f"metadata must contain one {selected_platform} artifact")
        else:
            raw_candidate = matches[0]
            filename = str(raw_candidate.get("filename", ""))
            artifact_source = _resolve_artifact_source(
                metadata_source,
                str(raw_candidate.get("url", "")),
                filename,
                remote_metadata=remote,
            )
            candidate = UpdateCandidate(
                platform=selected_platform,
                filename=filename,
                source=artifact_source,
                size_bytes=int(raw_candidate.get("size_bytes", 0)),
                sha256=str(raw_candidate.get("sha256", "")),
            )
        available = (
            not errors
            and candidate is not None
            and compare_release_versions(latest_version, normalized_current) > 0
        )
        return ApplicationUpdateCheck(
            metadata_source=metadata_source,
            current_version=normalized_current,
            latest_version=latest_version,
            requested_channel=requested_channel,
            published_channel=published_channel,
            platform=selected_platform,
            update_available=available,
            metadata_signed=metadata_signed,
            signature_valid=signature_valid,
            candidate=candidate,
            errors=tuple(errors),
        )
    except (OSError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        return ApplicationUpdateCheck(
            metadata_source=metadata_source,
            current_version=current_version,
            latest_version=latest_version,
            requested_channel=channel,
            published_channel=published_channel,
            platform=selected_platform,
            update_available=False,
            metadata_signed=metadata_signed,
            signature_valid=signature_valid,
            candidate=candidate,
            errors=tuple(errors),
        )


def _open_artifact_stream(
    source: str,
    *,
    timeout: float,
    opener: Callable[..., object],
) -> tuple[BinaryIO, Callable[[], None]]:
    parsed = urlparse(source)
    if parsed.scheme.casefold() == "file":
        if parsed.netloc not in ("", "localhost"):
            raise ValueError("file update artifact URL must not reference a remote host")
        path = Path(url2pathname(unquote(parsed.path)))
        handle = path.open("rb")
        return handle, handle.close
    _validate_https_url(source, label="update artifact URL")
    request = Request(
        source,
        headers={"Accept": "application/octet-stream", "User-Agent": USER_AGENT},
    )
    response = opener(request, timeout=timeout)
    close = getattr(response, "close", _noop)
    try:
        final_url = str(getattr(response, "geturl", lambda: source)())
        _validate_https_url(final_url, label="redirected update artifact URL")
    except (TypeError, ValueError):
        close()
        raise
    return response, close  # type: ignore[return-value]


def _write_pending_manifest(
    check: ApplicationUpdateCheck,
    candidate: UpdateCandidate,
    staged_path: Path,
    destination: Path,
) -> Path:
    manifest = destination / "pending-update.json"
    payload = {
        "schema_version": UPDATE_STAGE_SCHEMA_VERSION,
        "current_version": check.current_version,
        "target_version": check.latest_version,
        "channel": check.published_channel,
        "platform": check.platform,
        "artifact": {
            "filename": candidate.filename,
            "path": staged_path.as_posix(),
            "size_bytes": candidate.size_bytes,
            "sha256": candidate.sha256,
            "source": candidate.source,
        },
    }
    atomic_write_text(manifest, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return manifest


def stage_application_update(
    check: ApplicationUpdateCheck,
    *,
    destination: Path = DEFAULT_UPDATE_STAGE_DIRECTORY,
    max_artifact_bytes: int = DEFAULT_ARTIFACT_LIMIT_BYTES,
    timeout: float = DEFAULT_UPDATE_TIMEOUT_SECONDS,
    opener: Callable[..., object] = urlopen,
) -> ApplicationUpdateStage:
    selected_destination = Path(destination).expanduser().absolute()
    if not check.is_clean:
        return ApplicationUpdateStage(
            check,
            selected_destination.as_posix(),
            None,
            None,
            False,
            False,
            0,
            None,
            ("update check failed; no artifact was staged",),
        )
    if not check.update_available or check.candidate is None:
        return ApplicationUpdateStage(
            check,
            selected_destination.as_posix(),
            None,
            None,
            False,
            False,
            0,
            None,
        )
    candidate = check.candidate
    if candidate.size_bytes < 1 or candidate.size_bytes > max_artifact_bytes:
        return ApplicationUpdateStage(
            check,
            selected_destination.as_posix(),
            None,
            None,
            False,
            False,
            0,
            None,
            (f"artifact size exceeds the {max_artifact_bytes}-byte staging limit",),
        )
    selected_destination.mkdir(parents=True, exist_ok=True)
    staged_path = selected_destination / candidate.filename
    if (
        staged_path.is_file()
        and not staged_path.is_symlink()
        and staged_path.stat().st_size == candidate.size_bytes
    ):
        existing_digest = hashlib.sha256()
        with staged_path.open("rb") as existing_handle:
            while chunk := existing_handle.read(1024 * 1024):
                existing_digest.update(chunk)
        existing_sha = existing_digest.hexdigest()
        if existing_sha == candidate.sha256:
            manifest = _write_pending_manifest(check, candidate, staged_path, selected_destination)
            return ApplicationUpdateStage(
                check,
                selected_destination.as_posix(),
                staged_path.as_posix(),
                manifest.as_posix(),
                False,
                True,
                candidate.size_bytes,
                existing_sha,
            )
    temporary_path: Path | None = None
    close: Callable[[], None] = _noop
    try:
        stream, close = _open_artifact_stream(
            candidate.source,
            timeout=timeout,
            opener=opener,
        )
        digest = hashlib.sha256()
        written = 0
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=selected_destination,
            prefix=f".{candidate.filename}.",
            suffix=".part",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > candidate.size_bytes or written > max_artifact_bytes:
                    raise ValueError("downloaded artifact exceeded its declared size")
                digest.update(chunk)
                handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        artifact_sha256 = digest.hexdigest()
        if written != candidate.size_bytes:
            raise ValueError("downloaded artifact size does not match update metadata")
        if artifact_sha256 != candidate.sha256:
            raise ValueError("downloaded artifact SHA-256 does not match update metadata")
        os.replace(temporary_path, staged_path)
        temporary_path = None
        manifest = _write_pending_manifest(check, candidate, staged_path, selected_destination)
        return ApplicationUpdateStage(
            check,
            selected_destination.as_posix(),
            staged_path.as_posix(),
            manifest.as_posix(),
            True,
            False,
            written,
            artifact_sha256,
        )
    except (OSError, TypeError, ValueError) as exc:
        return ApplicationUpdateStage(
            check,
            selected_destination.as_posix(),
            None,
            None,
            False,
            False,
            0,
            None,
            (str(exc),),
        )
    finally:
        close()
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
