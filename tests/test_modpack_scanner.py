from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from generator.modpack_scanner import inspect_mod_jar, scan_modpack


def _neoforge_jar(mod_id: str = "testmachine", name: str = "Test Machine") -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "META-INF/neoforge.mods.toml",
            'modLoader="javafml"\nloaderVersion="[1,)"\nlicense="MIT"\n'
            f'[[mods]]\nmodId="{mod_id}"\nversion="1.0.0"\n'
            f'displayName="{name}"\n',
        )
    return output.getvalue()


def test_inspect_neoforge_jar_without_executing_code() -> None:
    mods = inspect_mod_jar(_neoforge_jar(), "mods/testmachine-1.0.0.jar")
    assert len(mods) == 1
    assert mods[0].mod_id == "testmachine"
    assert mods[0].resolved
    assert mods[0].category == "technology"


def test_scan_modrinth_pack_builds_normalized_profile(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    with ZipFile(pack, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("modrinth.index.json", json.dumps({
            "formatVersion": 1,
            "game": "minecraft",
            "name": "Example Pack",
            "versionId": "1.0",
            "dependencies": {"minecraft": "1.21.1", "neoforge": "21.1.1"},
            "files": [
                {"path": "mods/mekanism-10.7.0.jar", "hashes": {"sha1": "a" * 40}},
                {"path": "mods/architectury-api-13.0.0.jar", "hashes": {"sha1": "b" * 40}},
            ],
        }))

    result = scan_modpack(pack)
    assert result.is_clean
    assert result.source_format == "modrinth-mrpack"
    assert result.minecraft_version == "1.21.1"
    assert result.loader == "NeoForge"
    assert len(result.mods) == 2
    assert len(result.content_mods) == 1
    assert len(result.library_mods) == 1
    assert result.quest_target["target"] >= 42
    assert json.loads(result.format_json())["summary"]["mods"] == 2


def test_scan_curseforge_manifest_preserves_remote_references(tmp_path: Path) -> None:
    pack = tmp_path / "curseforge.zip"
    with ZipFile(pack, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps({
            "name": "Curse Example",
            "version": "2.0",
            "minecraft": {
                "version": "1.20.1",
                "modLoaders": [{"id": "forge-47.2.0", "primary": True}],
            },
            "files": [{"projectID": 42, "fileID": 99, "required": True}],
        }))

    result = scan_modpack(pack)
    assert result.is_clean
    assert result.loader == "Forge"
    assert result.mods[0].source_reference == "curseforge:42:99"
    assert not result.mods[0].resolved


def test_scan_plain_mods_directory_reads_embedded_metadata(tmp_path: Path) -> None:
    mods = tmp_path / "mods"
    mods.mkdir()
    (mods / "testmachine.jar").write_bytes(_neoforge_jar())

    result = scan_modpack(mods)
    assert result.is_clean
    assert result.source_format == "mods-directory"
    assert result.mods[0].display_name == "Test Machine"


def test_scan_missing_and_corrupt_inputs_report_errors(tmp_path: Path) -> None:
    missing = scan_modpack(tmp_path / "missing.zip")
    assert not missing.is_clean
    broken_path = tmp_path / "broken.zip"
    broken_path.write_bytes(b"broken")
    broken = scan_modpack(broken_path)
    assert not broken.is_clean
    assert broken.source_format == "invalid-archive"
