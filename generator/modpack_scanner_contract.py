from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from generator.modpack_scanner import scan_modpack


@dataclass(frozen=True, slots=True)
class ModpackScannerContract:
    modrinth_detected: bool
    curseforge_detected: bool
    neoforge_jar_resolved: bool
    loader_detection_clean: bool
    quest_target_generated: bool
    corrupt_archive_rejected: bool

    @property
    def is_clean(self) -> bool:
        return all((
            self.modrinth_detected,
            self.curseforge_detected,
            self.neoforge_jar_resolved,
            self.loader_detection_clean,
            self.quest_target_generated,
            self.corrupt_archive_rejected,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "modrinth_detected": self.modrinth_detected,
            "curseforge_detected": self.curseforge_detected,
            "neoforge_jar_resolved": self.neoforge_jar_resolved,
            "loader_detection_clean": self.loader_detection_clean,
            "quest_target_generated": self.quest_target_generated,
            "corrupt_archive_rejected": self.corrupt_archive_rejected,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Modpack scanner contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Modrinth format detected: {'yes' if self.modrinth_detected else 'no'}.",
            f"CurseForge format detected: {'yes' if self.curseforge_detected else 'no'}.",
            f"NeoForge JAR metadata resolved: {'yes' if self.neoforge_jar_resolved else 'no'}.",
            f"Loader detection clean: {'yes' if self.loader_detection_clean else 'no'}.",
            f"Quest target generated: {'yes' if self.quest_target_generated else 'no'}.",
            f"Corrupt archive rejected: {'yes' if self.corrupt_archive_rejected else 'no'}.",
        ))


def _jar_bytes() -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "META-INF/neoforge.mods.toml",
            'modLoader="javafml"\nloaderVersion="[1,)"\nlicense="MIT"\n'
            '[[mods]]\nmodId="exampletech"\nversion="1.2.3"\n'
            'displayName="Example Tech"\n',
        )
    return output.getvalue()


def run_modpack_scanner_contract() -> ModpackScannerContract:
    with TemporaryDirectory(prefix="modpack-scanner-contract-") as temporary:
        root = Path(temporary)
        mrpack = root / "sample.mrpack"
        with ZipFile(mrpack, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("modrinth.index.json", json.dumps({
                "formatVersion": 1,
                "game": "minecraft",
                "name": "Sample Modrinth Pack",
                "versionId": "1.0.0",
                "dependencies": {"minecraft": "1.21.1", "neoforge": "21.1.0"},
                "files": [
                    {"path": "mods/exampletech-1.2.3.jar", "hashes": {"sha1": "0" * 40}},
                    {"path": "mods/examplemagic-2.0.0.jar", "hashes": {"sha1": "1" * 40}},
                ],
            }))
        modrinth = scan_modpack(mrpack)

        curseforge = root / "curseforge.zip"
        with ZipFile(curseforge, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps({
                "name": "Sample CurseForge Pack",
                "version": "2.0.0",
                "minecraft": {
                    "version": "1.21.1",
                    "modLoaders": [{"id": "neoforge-21.1.0", "primary": True}],
                },
                "files": [{"projectID": 1234, "fileID": 5678, "required": True}],
            }))
        curseforge_profile = scan_modpack(curseforge)

        instance = root / "instance"
        mods = instance / "mods"
        mods.mkdir(parents=True)
        (mods / "exampletech-1.2.3.jar").write_bytes(_jar_bytes())
        local = scan_modpack(instance)

        corrupt = root / "broken.zip"
        corrupt.write_bytes(b"not a zip")
        broken = scan_modpack(corrupt)

    return ModpackScannerContract(
        modrinth_detected=(
            modrinth.is_clean
            and modrinth.source_format == "modrinth-mrpack"
            and len(modrinth.mods) == 2
        ),
        curseforge_detected=(
            curseforge_profile.is_clean
            and curseforge_profile.source_format == "curseforge-zip"
            and len(curseforge_profile.mods) == 1
        ),
        neoforge_jar_resolved=(
            local.is_clean
            and len(local.mods) == 1
            and local.mods[0].mod_id == "exampletech"
            and local.mods[0].resolved
        ),
        loader_detection_clean=(
            modrinth.minecraft_version == "1.21.1"
            and modrinth.loader == "NeoForge"
            and modrinth.loader_version == "21.1.0"
            and curseforge_profile.loader == "NeoForge"
        ),
        quest_target_generated=modrinth.quest_target["target"] > 0,
        corrupt_archive_rejected=(not broken.is_clean and broken.source_format == "invalid-archive"),
    )
