from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Callable, Sequence

from generator.output_writer import atomic_write_text

APPLY_SCHEMA_VERSION = "1.0"


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _load_pending(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
        raise ValueError("unsupported pending update manifest")
    artifact = payload.get("artifact")
    if not isinstance(artifact, dict):
        raise ValueError("pending update manifest has no artifact")
    return payload


def _verified_artifact(manifest_path: Path, payload: dict[str, object]) -> Path:
    artifact = payload["artifact"]
    assert isinstance(artifact, dict)
    path = Path(str(artifact.get("path", ""))).expanduser().absolute()
    stage_root = manifest_path.parent.absolute()
    try:
        path.relative_to(stage_root)
    except ValueError as exc:
        raise ValueError("staged artifact escapes the update directory") from exc
    if not path.is_file() or path.is_symlink():
        raise ValueError("staged artifact is missing or unsafe")
    expected_size = int(artifact.get("size_bytes", 0))
    expected_digest = str(artifact.get("sha256", ""))
    if path.stat().st_size != expected_size:
        raise ValueError("staged artifact size does not match the manifest")
    if _digest(path) != expected_digest:
        raise ValueError("staged artifact SHA-256 does not match the manifest")
    return path


@dataclass(frozen=True, slots=True)
class UpdateApplyResult:
    platform: str
    target_version: str
    applied: bool
    rollback_available: bool
    artifact_path: str
    target_path: str | None
    rollback_manifest: str | None
    command: tuple[str, ...]
    errors: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "platform": self.platform,
            "target_version": self.target_version,
            "applied": self.applied,
            "rollback_available": self.rollback_available,
            "artifact_path": self.artifact_path,
            "target_path": self.target_path,
            "rollback_manifest": self.rollback_manifest,
            "command": list(self.command),
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Application update apply: {'PASS' if self.is_clean else 'FAIL'}",
            f"Platform: {self.platform}.",
            f"Target version: {self.target_version}.",
            f"Applied: {'yes' if self.applied else 'no'}.",
            f"Rollback available: {'yes' if self.rollback_available else 'no'}.",
        ]
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


def apply_staged_update(
    manifest_path: Path,
    *,
    current_executable: Path | None = None,
    execute: bool = False,
    runner: Callable[[Sequence[str]], int] | None = None,
) -> UpdateApplyResult:
    manifest_path = Path(manifest_path).expanduser().absolute()
    platform = "unknown"
    target_version = "unknown"
    artifact_path = ""
    target_path: str | None = None
    rollback_manifest: str | None = None
    command: tuple[str, ...] = ()
    try:
        payload = _load_pending(manifest_path)
        platform = str(payload.get("platform", "")).casefold()
        target_version = str(payload.get("target_version", ""))
        artifact = _verified_artifact(manifest_path, payload)
        artifact_path = artifact.as_posix()
        if platform == "windows":
            command = (str(artifact), "/SILENT", "/NORESTART")
            applied = False
            if execute:
                selected_runner = runner or (
                    lambda args: subprocess.run(args, check=False).returncode
                )
                code = selected_runner(command)
                if code != 0:
                    raise ValueError(f"installer exited with status {code}")
                applied = True
            return UpdateApplyResult(
                platform,
                target_version,
                applied,
                False,
                artifact_path,
                None,
                None,
                command,
            )
        if platform != "linux":
            raise ValueError("update apply supports only Windows and Linux")
        if current_executable is None:
            raise ValueError("Linux update apply requires the current AppImage path")
        target = Path(current_executable).expanduser().absolute()
        target_path = target.as_posix()
        if not target.is_file() or target.is_symlink():
            raise ValueError("current AppImage is missing or unsafe")
        backup = manifest_path.parent / f"{target.name}.rollback"
        rollback = manifest_path.parent / "rollback-update.json"
        if execute:
            shutil.copy2(target, backup)
            temp = target.with_name(f".{target.name}.update")
            shutil.copy2(artifact, temp)
            os.chmod(temp, target.stat().st_mode)
            os.replace(temp, target)
            rollback_payload = {
                "schema_version": APPLY_SCHEMA_VERSION,
                "platform": "linux",
                "target_version": target_version,
                "target_path": target.as_posix(),
                "backup_path": backup.as_posix(),
                "installed_sha256": _digest(target),
            }
            atomic_write_text(
                rollback,
                json.dumps(rollback_payload, indent=2, sort_keys=True) + "\n",
            )
            rollback_manifest = rollback.as_posix()
        return UpdateApplyResult(
            platform,
            target_version,
            execute,
            execute,
            artifact_path,
            target_path,
            rollback_manifest,
            command,
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return UpdateApplyResult(
            platform,
            target_version,
            False,
            False,
            artifact_path,
            target_path,
            rollback_manifest,
            command,
            (str(exc),),
        )


def rollback_applied_update(
    manifest_path: Path,
    *,
    execute: bool = False,
) -> UpdateApplyResult:
    path = Path(manifest_path).expanduser().absolute()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema_version") != APPLY_SCHEMA_VERSION:
            raise ValueError("unsupported rollback manifest")
        target = Path(str(payload.get("target_path", ""))).absolute()
        backup = Path(str(payload.get("backup_path", ""))).absolute()
        if not backup.is_file() or backup.is_symlink():
            raise ValueError("rollback backup is missing or unsafe")
        if execute:
            temp = target.with_name(f".{target.name}.rollback")
            shutil.copy2(backup, temp)
            os.replace(temp, target)
        return UpdateApplyResult(
            "linux",
            str(payload.get("target_version", "")),
            execute,
            backup.is_file(),
            backup.as_posix(),
            target.as_posix(),
            path.as_posix(),
            (),
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return UpdateApplyResult(
            "unknown", "unknown", False, False, "", None, None, (), (str(exc),)
        )
