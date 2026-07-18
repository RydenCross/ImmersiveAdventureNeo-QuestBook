from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping

from generator.editor_model import EditorDocument, validate_editor_document
from generator.output_writer import atomic_write_text

RECOVERY_SCHEMA_VERSION = "1.0"
DEFAULT_RECOVERY_DIRECTORY = Path(".recovery")
DEFAULT_AUTOSAVE_FILE = Path("autosave.json")
DEFAULT_SNAPSHOT_DIRECTORY = Path("snapshots")
DEFAULT_MAX_SNAPSHOTS = 20
MAX_RECOVERY_REASON_LENGTH = 80


def _document_digest(document: EditorDocument) -> str:
    return sha256(document.format_json().encode("utf-8")).hexdigest()


def _safe_snapshot_name(value: str) -> str:
    name = value.strip()
    if not name or name in {".", ".."}:
        raise ValueError("snapshot name is required")
    if Path(name).name != name or "/" in name or "\\" in name:
        raise ValueError("snapshot name must not contain path components")
    if not name.endswith(".json"):
        raise ValueError("snapshot name must end with .json")
    return name


def _validated_reason(reason: str) -> str:
    cleaned = reason.strip() or "manual"
    if len(cleaned) > MAX_RECOVERY_REASON_LENGTH:
        raise ValueError(
            f"recovery reason must contain at most {MAX_RECOVERY_REASON_LENGTH} characters"
        )
    if any(ord(character) < 32 for character in cleaned):
        raise ValueError("recovery reason contains control characters")
    return cleaned


@dataclass(frozen=True, slots=True)
class RecoveryRecord:
    path: Path
    reason: str
    revision: int
    checksum: str
    document: EditorDocument

    def metadata(self, *, relative_to: Path | None = None) -> dict[str, object]:
        path = self.path
        if relative_to is not None:
            try:
                path = path.relative_to(relative_to)
            except ValueError:
                pass
        return {
            "path": path.as_posix(),
            "reason": self.reason,
            "revision": self.revision,
            "sha256": self.checksum,
        }


class EditorRecoveryStore:
    """Atomic autosave and bounded project snapshots inside an editor workspace."""

    def __init__(
        self,
        workspace: Path,
        *,
        max_snapshots: int = DEFAULT_MAX_SNAPSHOTS,
    ) -> None:
        if max_snapshots <= 0:
            raise ValueError("max_snapshots must be positive")
        self.workspace = Path(workspace).resolve()
        self.root = self.workspace / DEFAULT_RECOVERY_DIRECTORY
        self.autosave_path = self.root / DEFAULT_AUTOSAVE_FILE
        self.snapshot_directory = self.root / DEFAULT_SNAPSHOT_DIRECTORY
        self.max_snapshots = max_snapshots

    def _payload(self, document: EditorDocument, reason: str) -> dict[str, object]:
        validation = validate_editor_document(document)
        if document.errors or validation.errors:
            errors = tuple(document.errors) + validation.errors
            raise ValueError("cannot save invalid recovery document: " + "; ".join(errors))
        return {
            "schema_version": RECOVERY_SCHEMA_VERSION,
            "reason": _validated_reason(reason),
            "revision": document.revision,
            "sha256": _document_digest(document),
            "document": document.to_dict(),
        }

    def _write(self, path: Path, document: EditorDocument, reason: str) -> RecoveryRecord:
        payload = self._payload(document, reason)
        atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return RecoveryRecord(
            path=path,
            reason=str(payload["reason"]),
            revision=int(payload["revision"]),
            checksum=str(payload["sha256"]),
            document=document,
        )

    def _read(self, path: Path) -> RecoveryRecord:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid recovery record: {path.name}") from exc
        if not isinstance(payload, Mapping):
            raise ValueError(f"invalid recovery record: {path.name}")
        if payload.get("schema_version") != RECOVERY_SCHEMA_VERSION:
            raise ValueError(f"unsupported recovery schema in {path.name}")
        raw_document = payload.get("document")
        if not isinstance(raw_document, Mapping):
            raise ValueError(f"recovery record has no editor document: {path.name}")
        document = EditorDocument.from_dict(raw_document)
        validation = validate_editor_document(document)
        if document.errors or validation.errors:
            errors = tuple(document.errors) + validation.errors
            raise ValueError("invalid recovered editor document: " + "; ".join(errors))
        checksum = str(payload.get("sha256", ""))
        actual = _document_digest(document)
        if checksum != actual:
            raise ValueError(f"recovery checksum mismatch: {path.name}")
        revision = int(payload.get("revision", -1))
        if revision != document.revision:
            raise ValueError(f"recovery revision mismatch: {path.name}")
        return RecoveryRecord(
            path=path,
            reason=str(payload.get("reason", "unknown")),
            revision=revision,
            checksum=checksum,
            document=document,
        )

    def autosave(self, document: EditorDocument, *, reason: str) -> RecoveryRecord:
        return self._write(self.autosave_path, document, reason)

    def create_snapshot(
        self,
        document: EditorDocument,
        *,
        reason: str = "manual",
    ) -> RecoveryRecord:
        checksum = _document_digest(document)
        filename = f"revision-{document.revision:08d}-{checksum[:12]}.json"
        path = self.snapshot_directory / filename
        record = self._write(path, document, reason)
        self._prune_snapshots()
        return record

    def _snapshot_paths(self) -> tuple[Path, ...]:
        if not self.snapshot_directory.is_dir():
            return ()
        return tuple(sorted(self.snapshot_directory.glob("*.json")))

    def _prune_snapshots(self) -> None:
        records: list[RecoveryRecord] = []
        invalid: list[Path] = []
        for path in self._snapshot_paths():
            try:
                records.append(self._read(path))
            except ValueError:
                invalid.append(path)
        for path in invalid:
            path.unlink(missing_ok=True)
        ordered = sorted(records, key=lambda item: (item.revision, item.path.name))
        for record in ordered[: max(0, len(ordered) - self.max_snapshots)]:
            record.path.unlink(missing_ok=True)

    def list_snapshots(self) -> tuple[RecoveryRecord, ...]:
        records: list[RecoveryRecord] = []
        for path in self._snapshot_paths():
            try:
                records.append(self._read(path))
            except ValueError:
                continue
        return tuple(
            sorted(records, key=lambda item: (item.revision, item.path.name), reverse=True)
        )

    def load_autosave(self) -> RecoveryRecord:
        if not self.autosave_path.is_file():
            raise ValueError("no autosave recovery document is available")
        return self._read(self.autosave_path)

    def load_snapshot(self, name: str) -> RecoveryRecord:
        safe_name = _safe_snapshot_name(name)
        path = (self.snapshot_directory / safe_name).resolve()
        if not path.is_relative_to(self.snapshot_directory.resolve()):
            raise ValueError("snapshot path must remain inside the recovery directory")
        if not path.is_file():
            raise ValueError(f"snapshot does not exist: {safe_name}")
        return self._read(path)

    def clear_autosave(self) -> None:
        self.autosave_path.unlink(missing_ok=True)

    def discard(self, *, keep_snapshots: bool = True) -> None:
        self.clear_autosave()
        if not keep_snapshots and self.snapshot_directory.is_dir():
            for path in self.snapshot_directory.glob("*.json"):
                path.unlink(missing_ok=True)

    def status(self) -> dict[str, object]:
        autosave: dict[str, object] | None = None
        autosave_error: str | None = None
        if self.autosave_path.is_file():
            try:
                autosave = self._read(self.autosave_path).metadata(relative_to=self.workspace)
            except ValueError as exc:
                autosave_error = str(exc)
        snapshots = self.list_snapshots()
        return {
            "status": "fail" if autosave_error else "pass",
            "autosave_available": autosave is not None,
            "autosave": autosave,
            "autosave_error": autosave_error,
            "snapshot_count": len(snapshots),
            "max_snapshots": self.max_snapshots,
            "latest_snapshot": (
                snapshots[0].metadata(relative_to=self.workspace) if snapshots else None
            ),
            "snapshots": [
                record.metadata(relative_to=self.workspace) for record in snapshots
            ],
        }
