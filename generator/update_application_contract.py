from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tempfile

from generator.update_application import apply_staged_update, rollback_applied_update


@dataclass(frozen=True, slots=True)
class UpdateApplicationContract:
    dry_run_safe: bool
    linux_apply_verified: bool
    rollback_verified: bool
    tamper_rejected: bool
    windows_handoff_verified: bool

    @property
    def is_clean(self) -> bool:
        return all(
            (
                self.dry_run_safe,
                self.linux_apply_verified,
                self.rollback_verified,
                self.tamper_rejected,
                self.windows_handoff_verified,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "dry_run_safe": self.dry_run_safe,
            "linux_apply_verified": self.linux_apply_verified,
            "rollback_verified": self.rollback_verified,
            "tamper_rejected": self.tamper_rejected,
            "windows_handoff_verified": self.windows_handoff_verified,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return f"Update apply and rollback contract: {'PASS' if self.is_clean else 'FAIL'}"


def _manifest(root: Path, platform: str, artifact: Path) -> Path:
    payload = {
        "schema_version": "1.0",
        "current_version": "1.0.0",
        "target_version": "1.1.0",
        "channel": "stable",
        "platform": platform,
        "artifact": {
            "filename": artifact.name,
            "path": artifact.as_posix(),
            "size_bytes": artifact.stat().st_size,
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            "source": artifact.as_uri(),
        },
    }
    path = root / "pending-update.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def run_update_application_contract() -> UpdateApplicationContract:
    with tempfile.TemporaryDirectory(prefix="ftbq-update-apply-") as temporary:
        root = Path(temporary)
        artifact = root / "new.AppImage"
        artifact.write_bytes(b"new")
        current = root / "current.AppImage"
        current.write_bytes(b"old")
        manifest = _manifest(root, "linux", artifact)
        dry = apply_staged_update(manifest, current_executable=current)
        applied = apply_staged_update(
            manifest, current_executable=current, execute=True
        )
        rollback = rollback_applied_update(
            Path(applied.rollback_manifest or ""), execute=True
        )
        artifact.write_bytes(b"tampered")
        tampered = apply_staged_update(
            manifest, current_executable=current, execute=True
        )
        windows_artifact = root / "setup.exe"
        windows_artifact.write_bytes(b"installer")
        windows_manifest = _manifest(root, "windows", windows_artifact)
        calls: list[tuple[str, ...]] = []
        windows = apply_staged_update(
            windows_manifest,
            execute=True,
            runner=lambda args: (calls.append(tuple(args)) or 0),
        )
        return UpdateApplicationContract(
            dry_run_safe=not dry.applied and current.read_bytes() == b"old",
            linux_apply_verified=applied.is_clean and applied.applied,
            rollback_verified=rollback.is_clean and current.read_bytes() == b"old",
            tamper_rejected=not tampered.is_clean,
            windows_handoff_verified=windows.is_clean and windows.applied and bool(calls),
        )
