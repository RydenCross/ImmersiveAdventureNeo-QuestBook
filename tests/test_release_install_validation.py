from __future__ import annotations

import hashlib
import json
from pathlib import Path

from generator.release_install_validation import validate_release_installers
from generator.release_attestation import create_cyclonedx_sbom, create_slsa_provenance


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    assets = tmp_path / "assets"
    assets.mkdir()
    exe = assets / "FTBQuestMaker-1.2.3-Setup.exe"
    app = assets / "FTBQuestMaker-1.2.3-x86_64.AppImage"
    exe.write_bytes(b"MZ" + b"x" * 5000)
    app.write_bytes(b"\x7fELF" + b"y" * 5000)
    app.chmod(0o755)
    update = assets / "update.json"
    update.write_text(json.dumps({
        "windows": {"filename": exe.name, "sha256": _digest(exe)},
        "linux": {"filename": app.name, "sha256": _digest(app)},
    }), encoding="utf-8")
    sbom = assets / "ftb-quest-maker-sbom.cdx.json"
    sbom.write_text(json.dumps(create_cyclonedx_sbom([exe, app], version="v1.2.3")), encoding="utf-8")
    provenance = assets / "ftb-quest-maker-provenance.intoto.jsonl"
    provenance.write_text(json.dumps(create_slsa_provenance(
        [exe, app], repository="https://github.com/example/project", revision="a" * 40,
        workflow=".github/workflows/publish-release.yml"
    )) + "\n", encoding="utf-8")
    checksums = assets / "SHA256SUMS"
    checksums.write_text("".join(
        f"{_digest(path)}  {path.name}\n"
        for path in sorted((exe, app, update, sbom, provenance), key=lambda item: item.name)
    ), encoding="utf-8")
    return assets, checksums, update


def test_valid_release_installers_pass(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    result = validate_release_installers(assets, checksums, update)
    assert result.is_clean
    assert len(result.verified_files) == 5


def test_rejects_bad_signature_and_checksum(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    exe = next(assets.glob("*.exe"))
    exe.write_bytes(b"NO" + b"z" * 5000)
    result = validate_release_installers(assets, checksums, update)
    assert not result.is_clean
    assert any("MZ signature" in error for error in result.errors)
    assert any("checksum mismatch" in error for error in result.errors)


def test_rejects_missing_platform_artifact(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    next(assets.glob("*.AppImage")).unlink()
    result = validate_release_installers(assets, checksums, update)
    assert not result.is_clean
    assert any("exactly one Linux" in error for error in result.errors)


def test_rejects_unexpected_asset_and_incomplete_manifest(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    extra = assets / "debug.log"
    extra.write_text("not for publication", encoding="utf-8")
    result = validate_release_installers(assets, checksums, update)
    assert not result.is_clean
    assert any("unexpected release asset: debug.log" in error for error in result.errors)
    assert any("missing staged asset" in error for error in result.errors)


def test_rejects_duplicate_basenames_and_symlinks(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    nested = assets / "nested"
    nested.mkdir()
    duplicate = nested / next(assets.glob("*.exe")).name
    duplicate.write_bytes(b"MZ" + b"q" * 5000)
    try:
        (assets / "linked-update.json").symlink_to(update.name)
    except OSError:
        pass
    result = validate_release_installers(assets, checksums, update)
    assert not result.is_clean
    assert any("duplicate release asset basename" in error for error in result.errors)
    if (assets / "linked-update.json").is_symlink():
        assert any("symbolic links are not allowed" in error for error in result.errors)


def test_requires_complete_release_metadata_set(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    next(assets.glob("*.cdx.json")).unlink()
    next(assets.glob("*.intoto.jsonl")).unlink()
    result = validate_release_installers(assets, checksums, update)
    assert not result.is_clean
    assert any("CycloneDX SBOM" in error for error in result.errors)
    assert any("provenance statement" in error for error in result.errors)


def test_rejects_nested_allowlisted_asset(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    exe = next(assets.glob("*.exe"))
    nested = assets / "nested"
    nested.mkdir()
    moved = nested / exe.name
    exe.replace(moved)
    result = validate_release_installers(assets, checksums, update)
    assert not result.is_clean
    assert any("stored directly in the asset root" in error for error in result.errors)


def test_rejects_external_metadata_paths(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    external_checksums = tmp_path / "SHA256SUMS"
    external_checksums.write_bytes(checksums.read_bytes())
    external_update = tmp_path / "update.json"
    external_update.write_bytes(update.read_bytes())
    result = validate_release_installers(assets, external_checksums, external_update)
    assert not result.is_clean
    assert any("checksum manifest must be" in error for error in result.errors)
    assert any("update metadata must be" in error for error in result.errors)


def test_rejects_tampered_non_installer_assets(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    sbom = next(assets.glob("*.cdx.json"))
    provenance = next(assets.glob("*.intoto.jsonl"))
    sbom.write_text('{"tampered": true}', encoding="utf-8")
    provenance.write_text('{"tampered": true}', encoding="utf-8")
    result = validate_release_installers(assets, checksums, update)
    assert not result.is_clean
    assert any(f"checksum mismatch for {sbom.name}" in error for error in result.errors)
    assert any(f"checksum mismatch for {provenance.name}" in error for error in result.errors)


def test_rejects_tampered_update_metadata_even_when_json_is_valid(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    payload = json.loads(update.read_text(encoding="utf-8"))
    payload["channel"] = "tampered"
    update.write_text(json.dumps(payload), encoding="utf-8")
    result = validate_release_installers(assets, checksums, update)
    assert not result.is_clean
    assert any("checksum mismatch for update.json" in error for error in result.errors)


def test_rejects_semantically_unbound_sbom_and_provenance(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    exe = next(assets.glob("*.exe"))
    sbom = next(assets.glob("*.cdx.json"))
    payload = json.loads(sbom.read_text(encoding="utf-8"))
    for component in payload["components"]:
        if component.get("name") == exe.name:
            component["hashes"][0]["content"] = "0" * 64
    sbom.write_text(json.dumps(payload), encoding="utf-8")
    provenance = next(assets.glob("*.intoto.jsonl"))
    provenance_payload = json.loads(provenance.read_text(encoding="utf-8"))
    provenance_payload["predicate"]["buildDefinition"]["externalParameters"]["ref"] = "b" * 40
    provenance.write_text(json.dumps(provenance_payload) + "\n", encoding="utf-8")
    checksums.write_text("".join(
        f"{_digest(path)}  {path.name}\n"
        for path in sorted((next(assets.glob("*.exe")), next(assets.glob("*.AppImage")), update, sbom, provenance), key=lambda item: item.name)
    ), encoding="utf-8")
    result = validate_release_installers(
        assets, checksums, update, expected_revision="a" * 40,
        expected_repository="https://github.com/example/project"
    )
    assert not result.is_clean
    assert any("SBOM does not bind SHA-256" in error for error in result.errors)
    assert any("source revision" in error for error in result.errors)


def test_accepts_semantically_bound_release_metadata(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    result = validate_release_installers(
        assets, checksums, update, expected_revision="a" * 40,
        expected_repository="https://github.com/example/project"
    )
    assert result.is_clean
