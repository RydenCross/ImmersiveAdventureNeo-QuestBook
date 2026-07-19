from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import shutil
from tempfile import TemporaryDirectory
from typing import Mapping
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile, ZipInfo

from generator.editor_model import EditorDocument, editor_document_to_blueprint, validate_editor_document
from generator.ftb_blueprint_exporter import DEFAULT_FTB_QUESTS_VERSION, export_quest_blueprint
from generator.modpack_scanner import scan_modpack
from generator.parser import FTBQuestParser
from generator.validator import ProjectValidator

BUNDLE_SCHEMA_VERSION = "1.0"
BUNDLE_EXTENSION = ".ftbqproj"
MAX_BUNDLE_ENTRIES = 20_000
MAX_BUNDLE_BYTES = 512 * 1024 * 1024
_CANONICAL_DATE = (1980, 1, 1, 0, 0, 0)


def _json_bytes(payload: Mapping[str, object]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def _tree_digest(root: Path) -> str:
    result = sha256()
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda p: p.as_posix()):
        name = path.relative_to(root).as_posix()
        result.update(name.encode("utf-8"))
        result.update(b"\0")
        result.update(path.read_bytes())
        result.update(b"\0")
    return result.hexdigest()


def _source_fingerprint(document: EditorDocument) -> dict[str, object]:
    source = Path(document.source_path) if document.source_path else None
    payload: dict[str, object] = {
        "path": source.name if source else "",
        "format": document.source_format,
        "available": bool(source and source.exists()),
        "kind": "missing",
        "bytes": 0,
        "sha256": "",
    }
    if source is None or not source.exists():
        return payload
    if source.is_file():
        data = source.read_bytes()
        payload.update(kind="file", bytes=len(data), sha256=_digest(data))
        return payload
    result = sha256()
    total = 0
    for path in sorted((item for item in source.rglob("*") if item.is_file()), key=lambda p: p.as_posix()):
        relative = path.relative_to(source).as_posix()
        data = path.read_bytes()
        total += len(data)
        result.update(relative.encode("utf-8"))
        result.update(b"\0")
        result.update(_digest(data).encode("ascii"))
        result.update(b"\n")
    payload.update(kind="directory", bytes=total, sha256=result.hexdigest())
    return payload


def _safe_entry(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(
        name
        and not path.is_absolute()
        and "\\" not in name
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def _zip_write(archive: ZipFile, name: str, data: bytes) -> None:
    info = ZipInfo(name, date_time=_CANONICAL_DATE)
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = ZIP_DEFLATED
    archive.writestr(info, data)


@dataclass(frozen=True, slots=True)
class ProjectBundleResult:
    destination: str
    schema_version: str
    entries: int
    bytes: int
    sha256: str
    export_tree_sha256: str
    chapters: int
    quests: int
    errors: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "destination": self.destination,
            "schema_version": self.schema_version,
            "entries": self.entries,
            "bytes": self.bytes,
            "sha256": self.sha256,
            "export_tree_sha256": self.export_tree_sha256,
            "chapters": self.chapters,
            "quests": self.quests,
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Quest Maker project bundle: {'PASS' if self.is_clean else 'FAIL'}",
            f"Destination: {self.destination}.",
            f"Entries: {self.entries}.",
            f"Chapters: {self.chapters}.",
            f"Quests: {self.quests}.",
            f"Bundle SHA-256: {self.sha256 or '<none>'}.",
            *tuple(f"Error: {error}" for error in self.errors),
        ))


@dataclass(frozen=True, slots=True)
class ProjectBundleInspection:
    path: str
    schema_version: str
    entries: int
    chapters: int
    quests: int
    pack_name: str
    source_sha256: str
    export_tree_sha256: str
    missing_entries: tuple[str, ...]
    unexpected_entries: tuple[str, ...]
    changed_entries: tuple[str, ...]
    unsafe_entries: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.missing_entries, self.unexpected_entries, self.changed_entries,
                        self.unsafe_entries, self.errors))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "path": self.path,
            "schema_version": self.schema_version,
            "entries": self.entries,
            "chapters": self.chapters,
            "quests": self.quests,
            "pack_name": self.pack_name,
            "source_sha256": self.source_sha256,
            "export_tree_sha256": self.export_tree_sha256,
            "missing_entries": list(self.missing_entries),
            "unexpected_entries": list(self.unexpected_entries),
            "changed_entries": list(self.changed_entries),
            "unsafe_entries": list(self.unsafe_entries),
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Quest Maker project bundle inspection: {'PASS' if self.is_clean else 'FAIL'}",
            f"Path: {self.path}.",
            f"Pack: {self.pack_name or '<unknown>'}.",
            f"Entries: {self.entries}.",
            f"Missing entries: {len(self.missing_entries)}.",
            f"Unexpected entries: {len(self.unexpected_entries)}.",
            f"Changed entries: {len(self.changed_entries)}.",
            f"Unsafe entries: {len(self.unsafe_entries)}.",
            *tuple(f"Error: {error}" for error in self.errors),
        ))


@dataclass(frozen=True, slots=True)
class ProjectInstallResult:
    bundle: str
    instance: str
    destination: str
    backup: str
    installed_files: int
    dry_run: bool
    compatibility_warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "bundle": self.bundle,
            "instance": self.instance,
            "destination": self.destination,
            "backup": self.backup,
            "installed_files": self.installed_files,
            "dry_run": self.dry_run,
            "compatibility_warnings": list(self.compatibility_warnings),
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Quest Maker project installation: {'PASS' if self.is_clean else 'FAIL'}",
            f"Instance: {self.instance}.",
            f"Destination: {self.destination}.",
            f"Installed files: {self.installed_files}.",
            f"Dry run: {'yes' if self.dry_run else 'no'}.",
            f"Backup: {self.backup or '<none>'}.",
            *tuple(f"Warning: {warning}" for warning in self.compatibility_warnings),
            *tuple(f"Error: {error}" for error in self.errors),
        ))


def create_project_bundle(
    document: EditorDocument,
    destination: Path,
    *,
    settings: Mapping[str, object] | None = None,
    version: str = DEFAULT_FTB_QUESTS_VERSION,
) -> ProjectBundleResult:
    destination = Path(destination)
    errors: list[str] = []
    validation = validate_editor_document(document)
    if document.errors or validation.errors:
        errors.extend(tuple(document.errors) + validation.errors)
    if destination.suffix.casefold() != BUNDLE_EXTENSION:
        errors.append(f"project bundles must use the {BUNDLE_EXTENSION} extension")
    if errors:
        return ProjectBundleResult(destination.as_posix(), BUNDLE_SCHEMA_VERSION, 0, 0, "", "", 0, 0, tuple(errors))

    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="quest-project-bundle-", dir=destination.parent) as temporary:
        temp = Path(temporary)
        export_root = temp / "ftbquests"
        export = export_quest_blueprint(editor_document_to_blueprint(document), export_root, version=version)
        if not export.is_clean:
            return ProjectBundleResult(destination.as_posix(), BUNDLE_SCHEMA_VERSION, 0, 0, "", "", 0, 0, export.errors)

        portable_document = replace(
            document,
            source_path=Path(document.source_path).name if document.source_path else "",
        )
        payloads: dict[str, bytes] = {
            "project/editor-document.json": (portable_document.format_json() + "\n").encode("utf-8"),
            "project/settings.json": _json_bytes(dict(settings or {})),
            "source/fingerprint.json": _json_bytes(_source_fingerprint(document)),
        }
        for path in sorted((item for item in export_root.rglob("*") if item.is_file()), key=lambda p: p.as_posix()):
            payloads[f"export/ftbquests/{path.relative_to(export_root).as_posix()}"] = path.read_bytes()

        manifest = {
            "schema_version": BUNDLE_SCHEMA_VERSION,
            "application": "FTB Quest Maker",
            "pack": {
                "name": document.pack_name,
                "minecraft": document.minecraft_version,
                "loader": document.loader,
            },
            "document": {
                "schema_version": document.schema_version,
                "revision": document.revision,
                "chapters": len(document.chapters),
                "quests": len(document.quests),
                "dependency_edges": len(document.edges),
            },
            "export": {
                "ftb_quests_version": version,
                "tree_sha256": export.tree_sha256,
                "files": len(export.files),
            },
            "entries": {
                name: {"bytes": len(data), "sha256": _digest(data)}
                for name, data in sorted(payloads.items())
            },
        }
        payloads["manifest.json"] = _json_bytes(manifest)
        temporary_archive = temp / destination.name
        with ZipFile(temporary_archive, "w", compression=ZIP_DEFLATED) as archive:
            for name, data in sorted(payloads.items()):
                _zip_write(archive, name, data)
        os.replace(temporary_archive, destination)

    data = destination.read_bytes()
    return ProjectBundleResult(
        destination=destination.as_posix(),
        schema_version=BUNDLE_SCHEMA_VERSION,
        entries=len(payloads),
        bytes=len(data),
        sha256=_digest(data),
        export_tree_sha256=export.tree_sha256,
        chapters=len(document.chapters),
        quests=len(document.quests),
    )


def _read_bundle(path: Path) -> tuple[dict[str, object], dict[str, bytes], list[str]]:
    errors: list[str] = []
    payloads: dict[str, bytes] = {}
    try:
        with ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_BUNDLE_ENTRIES:
                raise ValueError("project bundle has too many entries")
            total = sum(info.file_size for info in infos)
            if total > MAX_BUNDLE_BYTES:
                raise ValueError("project bundle is too large")
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                errors.append("project bundle contains duplicate entries")
            for info in infos:
                if _safe_entry(info.filename):
                    payloads[info.filename] = archive.read(info)
            manifest_raw = payloads.get("manifest.json", b"")
            manifest = json.loads(manifest_raw.decode("utf-8"))
            if not isinstance(manifest, dict):
                raise ValueError("project bundle manifest must contain an object")
            return manifest, payloads, errors
    except (BadZipFile, OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return {}, payloads, errors + [str(exc)]


def inspect_project_bundle(path: Path) -> ProjectBundleInspection:
    path = Path(path)
    manifest, payloads, errors = _read_bundle(path)
    unsafe: tuple[str, ...] = ()
    try:
        with ZipFile(path) as archive:
            unsafe = tuple(sorted(info.filename for info in archive.infolist() if not _safe_entry(info.filename)))
    except (BadZipFile, OSError):
        pass

    entries = manifest.get("entries", {}) if isinstance(manifest, Mapping) else {}
    if not isinstance(entries, Mapping):
        entries = {}
        errors.append("project bundle manifest entries must contain an object")
    declared = set(str(name) for name in entries)
    actual = set(payloads) - {"manifest.json"}
    missing = tuple(sorted(declared - actual))
    unexpected = tuple(sorted(actual - declared))
    changed: list[str] = []
    for name in sorted(declared & actual):
        metadata = entries.get(name, {})
        if not isinstance(metadata, Mapping):
            changed.append(name)
            continue
        data = payloads[name]
        if metadata.get("bytes") != len(data) or metadata.get("sha256") != _digest(data):
            changed.append(name)

    document_payload = {}
    try:
        document_payload = json.loads(payloads["project/editor-document.json"].decode("utf-8"))
        document = EditorDocument.from_dict(document_payload)
        validation = validate_editor_document(document)
        if document.errors or validation.errors:
            errors.append("bundled editor document is invalid")
    except (KeyError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        errors.append(f"invalid bundled editor document: {exc}")
        document = None

    export_tree = ""
    export_files = {name: data for name, data in payloads.items() if name.startswith("export/ftbquests/")}
    if export_files:
        with TemporaryDirectory(prefix="quest-project-inspect-") as temporary:
            root = Path(temporary) / "ftbquests"
            for name, data in export_files.items():
                relative = PurePosixPath(name).relative_to(PurePosixPath("export/ftbquests"))
                target = root.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            export_tree = _tree_digest(root)
            try:
                quests_root = root if root.name == "quests" else root / "quests"
                project = FTBQuestParser().load(quests_root)
                report = ProjectValidator().validate(project)
                if not report.is_valid:
                    errors.append("bundled FTB Quests export failed validation")
            except (OSError, TypeError, ValueError) as exc:
                errors.append(f"invalid bundled FTB Quests export: {exc}")
    else:
        errors.append("project bundle does not contain an FTB Quests export")

    pack = manifest.get("pack", {}) if isinstance(manifest, Mapping) else {}
    doc_meta = manifest.get("document", {}) if isinstance(manifest, Mapping) else {}
    source = {}
    try:
        source = json.loads(payloads.get("source/fingerprint.json", b"{}").decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        errors.append("invalid source fingerprint")
    expected_tree = ""
    export_meta = manifest.get("export", {}) if isinstance(manifest, Mapping) else {}
    if isinstance(export_meta, Mapping):
        expected_tree = str(export_meta.get("tree_sha256", ""))
        if expected_tree and export_tree and expected_tree != export_tree:
            errors.append("bundled export tree digest does not match the manifest")

    return ProjectBundleInspection(
        path=path.as_posix(),
        schema_version=str(manifest.get("schema_version", "")) if isinstance(manifest, Mapping) else "",
        entries=len(payloads),
        chapters=int(doc_meta.get("chapters", 0)) if isinstance(doc_meta, Mapping) else 0,
        quests=int(doc_meta.get("quests", 0)) if isinstance(doc_meta, Mapping) else 0,
        pack_name=str(pack.get("name", "")) if isinstance(pack, Mapping) else "",
        source_sha256=str(source.get("sha256", "")) if isinstance(source, Mapping) else "",
        export_tree_sha256=export_tree,
        missing_entries=missing,
        unexpected_entries=unexpected,
        changed_entries=tuple(changed),
        unsafe_entries=unsafe,
        errors=tuple(errors),
    )


def load_project_bundle(path: Path) -> tuple[EditorDocument, ProjectBundleInspection]:
    inspection = inspect_project_bundle(path)
    if not inspection.is_clean:
        raise ValueError("invalid project bundle: " + "; ".join(
            (*inspection.errors, *inspection.missing_entries, *inspection.changed_entries, *inspection.unsafe_entries)
        ))
    _manifest, payloads, _errors = _read_bundle(Path(path))
    payload = json.loads(payloads["project/editor-document.json"].decode("utf-8"))
    return EditorDocument.from_dict(payload), inspection


def install_project_bundle(
    bundle: Path,
    instance: Path,
    *,
    backup: bool = True,
    dry_run: bool = False,
    force: bool = False,
) -> ProjectInstallResult:
    bundle = Path(bundle).resolve()
    instance = Path(instance).resolve()
    errors: list[str] = []
    compatibility_errors: list[str] = []
    warnings: list[str] = []
    backup_path = ""
    inspection = inspect_project_bundle(bundle)
    if not inspection.is_clean:
        errors.append("project bundle failed verification")
    if not instance.is_dir() or instance.is_symlink():
        errors.append("instance path must be an existing non-symlink directory")
    config = instance / "config"
    target = config / "ftbquests"
    if config.is_symlink() or target.is_symlink():
        errors.append("instance config and FTB Quests destinations must not be symlinks")
    if errors:
        return ProjectInstallResult(bundle.as_posix(), instance.as_posix(), target.as_posix(), "", 0, dry_run, (), tuple(errors))

    manifest, payloads, read_errors = _read_bundle(bundle)
    if read_errors:
        errors.extend(read_errors)
    pack = manifest.get("pack", {}) if isinstance(manifest, Mapping) else {}
    try:
        profile = scan_modpack(instance)
        expected_minecraft = str(pack.get("minecraft", "")) if isinstance(pack, Mapping) else ""
        expected_loader = str(pack.get("loader", "")) if isinstance(pack, Mapping) else ""
        if expected_minecraft and profile.minecraft_version and expected_minecraft != profile.minecraft_version:
            compatibility_errors.append(f"Minecraft version mismatch: bundle {expected_minecraft}, instance {profile.minecraft_version}")
        if expected_loader and profile.loader and expected_loader.casefold() != profile.loader.casefold():
            compatibility_errors.append(f"loader mismatch: bundle {expected_loader}, instance {profile.loader}")
        warnings.extend(profile.warnings)
    except (OSError, TypeError, ValueError) as exc:
        warnings.append(f"instance compatibility scan was incomplete: {exc}")
    if errors:
        return ProjectInstallResult(bundle.as_posix(), instance.as_posix(), target.as_posix(), "", 0, dry_run, tuple(warnings), tuple(errors))
    if compatibility_errors and not force:
        return ProjectInstallResult(bundle.as_posix(), instance.as_posix(), target.as_posix(), "", 0, dry_run, tuple(warnings), tuple(compatibility_errors))
    if force:
        warnings.extend(compatibility_errors)

    export_files = {name: data for name, data in payloads.items() if name.startswith("export/ftbquests/")}
    installed_files = len(export_files)
    if dry_run:
        return ProjectInstallResult(bundle.as_posix(), instance.as_posix(), target.as_posix(), "", installed_files, True, tuple(warnings), ())

    config.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".quest-maker-install-", dir=instance) as temporary:
        temp = Path(temporary)
        staged = temp / "ftbquests"
        for name, data in export_files.items():
            relative = PurePosixPath(name).relative_to(PurePosixPath("export/ftbquests"))
            destination = staged.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        project = FTBQuestParser().load(staged / "quests")
        report = ProjectValidator().validate(project)
        if not report.is_valid:
            return ProjectInstallResult(bundle.as_posix(), instance.as_posix(), target.as_posix(), "", 0, False, tuple(warnings), ("staged FTB Quests export failed validation",))

        previous = temp / "previous-ftbquests"
        try:
            if target.exists():
                if not target.is_dir():
                    raise ValueError("existing FTB Quests destination is not a directory")
                if any(path.is_symlink() for path in target.rglob("*")):
                    raise ValueError("existing FTB Quests destination contains symlinks")
                old_digest = _tree_digest(target)[:16]
                if backup:
                    backup_root = instance / ".quest-maker-backups"
                    if backup_root.is_symlink():
                        raise ValueError("quest maker backup directory must not be a symlink")
                    backup_root.mkdir(parents=True, exist_ok=True)
                    chosen_backup = backup_root / f"ftbquests-{old_digest}"
                    if not chosen_backup.exists():
                        shutil.copytree(target, chosen_backup)
                    backup_path = chosen_backup.as_posix()
                os.replace(target, previous)
            os.replace(staged, target)
            if previous.exists():
                shutil.rmtree(previous)
        except (OSError, ValueError) as exc:
            if target.exists() and previous.exists():
                shutil.rmtree(target, ignore_errors=True)
            if previous.exists() and not target.exists():
                os.replace(previous, target)
            errors.append(str(exc))

    return ProjectInstallResult(
        bundle=bundle.as_posix(),
        instance=instance.as_posix(),
        destination=target.as_posix(),
        backup=backup_path,
        installed_files=installed_files if not errors else 0,
        dry_run=False,
        compatibility_warnings=tuple(sorted(set(warnings))),
        errors=tuple(errors),
    )
