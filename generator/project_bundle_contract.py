from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from generator.editor_model import generate_editor_model
from generator.editor_service import EditorSession, handle_editor_api
from generator.editor_ui import EDITOR_HTML
from generator.modpack_content_scanner_contract import _synthetic_pack
from generator.project_bundle import (
    create_project_bundle,
    inspect_project_bundle,
    install_project_bundle,
    load_project_bundle,
)


@dataclass(frozen=True, slots=True)
class ProjectBundleContract:
    deterministic_bundle: bool
    verified_manifest: bool
    document_round_trip: bool
    tamper_detection: bool
    safe_installation: bool
    backup_preservation: bool
    api_routes: bool
    visual_controls: bool

    @property
    def is_clean(self) -> bool:
        return all((
            self.deterministic_bundle,
            self.verified_manifest,
            self.document_round_trip,
            self.tamper_detection,
            self.safe_installation,
            self.backup_preservation,
            self.api_routes,
            self.visual_controls,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "deterministic_bundle": self.deterministic_bundle,
            "verified_manifest": self.verified_manifest,
            "document_round_trip": self.document_round_trip,
            "tamper_detection": self.tamper_detection,
            "safe_installation": self.safe_installation,
            "backup_preservation": self.backup_preservation,
            "api_routes": self.api_routes,
            "visual_controls": self.visual_controls,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Portable project bundle contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Deterministic bundle: {'PASS' if self.deterministic_bundle else 'FAIL'}.",
            f"Verified manifest: {'PASS' if self.verified_manifest else 'FAIL'}.",
            f"Document round trip: {'PASS' if self.document_round_trip else 'FAIL'}.",
            f"Tamper detection: {'PASS' if self.tamper_detection else 'FAIL'}.",
            f"Safe installation: {'PASS' if self.safe_installation else 'FAIL'}.",
            f"Backup preservation: {'PASS' if self.backup_preservation else 'FAIL'}.",
            f"API routes: {'PASS' if self.api_routes else 'FAIL'}.",
            f"Visual controls: {'PASS' if self.visual_controls else 'FAIL'}.",
        ))


def run_project_bundle_contract() -> ProjectBundleContract:
    with TemporaryDirectory(prefix="project-bundle-contract-") as temporary:
        root = Path(temporary)
        pack = root / "contract.mrpack"
        _synthetic_pack(pack)
        document = generate_editor_model(
            pack,
            target_quests=4,
            chapter_size=10,
            reward_policy="conservative",
        )
        first = root / "first.ftbqproj"
        second = root / "second.ftbqproj"
        created = create_project_bundle(document, first, settings={"chapter_size": 10})
        create_project_bundle(document, second, settings={"chapter_size": 10})
        deterministic_bundle = created.is_clean and first.read_bytes() == second.read_bytes()
        inspection = inspect_project_bundle(first)
        verified_manifest = inspection.is_clean and inspection.quests == 4
        restored, restored_inspection = load_project_bundle(first)
        document_round_trip = restored_inspection.is_clean and restored.quest_count == 4

        tampered = root / "tampered.ftbqproj"
        with ZipFile(first) as source:
            entries = {info.filename: source.read(info) for info in source.infolist()}
        entries["project/settings.json"] = b'{"changed": true}\n'
        with ZipFile(tampered, "w", compression=ZIP_DEFLATED) as archive:
            for name, data in sorted(entries.items()):
                info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = ZIP_DEFLATED
                archive.writestr(info, data)
        tamper_detection = "project/settings.json" in inspect_project_bundle(tampered).changed_entries

        instance = root / "instance"
        legacy = instance / "config" / "ftbquests"
        legacy.mkdir(parents=True)
        (legacy / "legacy.txt").write_text("legacy", encoding="utf-8")
        installed = install_project_bundle(first, instance, force=True)
        safe_installation = installed.is_clean and (instance / "config/ftbquests/quests/data.snbt").is_file()
        backup_preservation = bool(
            installed.backup
            and (Path(installed.backup) / "legacy.txt").read_text(encoding="utf-8") == "legacy"
        )

        session = EditorSession(document, workspace=root / "workspace")
        bundle_response = handle_editor_api(
            session,
            "POST",
            "/api/v1/bundle",
            {"destination": "shared.ftbqproj"},
        )
        api_instance = root / "api-instance"
        api_instance.mkdir()
        install_response = handle_editor_api(
            session,
            "POST",
            "/api/v1/install",
            {"instance": api_instance.as_posix(), "bundle": "shared.ftbqproj", "force": True},
        )
        imported = session.import_project_bundle(
            "shared.ftbqproj",
            BytesIO((session.workspace / "shared.ftbqproj").read_bytes()),
            (session.workspace / "shared.ftbqproj").stat().st_size,
        )
        api_routes = bool(
            bundle_response.status_code == 200
            and install_response.status_code == 200
            and imported.get("status") == "pass"
        )
        visual_controls = all(token in EDITOR_HTML for token in (
            'id="bundle-button"',
            'id="install-button"',
            "/bundle",
            "/install",
            "/project-bundle-import",
            "saveBundle",
            "installQuestbook",
        ))

        return ProjectBundleContract(
            deterministic_bundle=deterministic_bundle,
            verified_manifest=verified_manifest,
            document_round_trip=document_round_trip,
            tamper_detection=tamper_detection,
            safe_installation=safe_installation,
            backup_preservation=backup_preservation,
            api_routes=api_routes,
            visual_controls=visual_controls,
        )
