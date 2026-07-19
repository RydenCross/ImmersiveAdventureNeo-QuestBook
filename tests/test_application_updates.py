from __future__ import annotations

import json
from pathlib import Path

from generator.application_updates import (
    check_for_application_update,
    compare_release_versions,
    stage_application_update,
)
from generator.desktop_packages import create_update_metadata, write_update_metadata


def _metadata(tmp_path: Path, *, version: str = "2.0.0") -> tuple[Path, Path, bytes]:
    artifact = tmp_path / f"FTBQuestMaker-{version}-Setup.exe"
    artifact.write_bytes(b"installer-bytes")
    key = b"test-update-key"
    metadata = create_update_metadata(
        version,
        "stable",
        {"windows": artifact},
        base_url=tmp_path.as_uri(),
        signing_key=key,
        key_id="test",
    )
    metadata_path = tmp_path / "latest.json"
    write_update_metadata(metadata, metadata_path)
    return metadata_path, artifact, key


def test_semantic_version_ordering_handles_prereleases() -> None:
    assert compare_release_versions("1.0.0", "1.0.0-beta.2") > 0
    assert compare_release_versions("1.0.0-beta.10", "1.0.0-beta.2") > 0
    assert compare_release_versions("1.0.0-alpha", "1.0.0-beta") < 0
    assert compare_release_versions("1.0.0+build.2", "1.0.0+build.1") == 0


def test_signed_local_metadata_selects_platform_update(tmp_path: Path) -> None:
    metadata_path, artifact, key = _metadata(tmp_path)
    result = check_for_application_update(
        metadata_path,
        "1.5.0",
        platform="windows",
        signing_key=key,
        require_signature=True,
    )
    assert result.is_clean
    assert result.update_available
    assert result.candidate is not None
    assert result.candidate.filename == artifact.name
    assert result.signature_valid is True


def test_current_version_is_not_offered_again(tmp_path: Path) -> None:
    metadata_path, _artifact, key = _metadata(tmp_path)
    result = check_for_application_update(
        metadata_path,
        "2.0.0",
        platform="windows",
        signing_key=key,
    )
    assert result.is_clean
    assert not result.update_available


def test_staging_is_atomic_verified_and_idempotent(tmp_path: Path) -> None:
    metadata_path, artifact, key = _metadata(tmp_path)
    check = check_for_application_update(
        metadata_path,
        "1.0.0",
        platform="windows",
        signing_key=key,
    )
    destination = tmp_path / "updates"
    first = stage_application_update(check, destination=destination)
    second = stage_application_update(check, destination=destination)
    assert first.is_clean and first.downloaded and first.staged
    assert Path(first.staged_path or "").read_bytes() == artifact.read_bytes()
    assert Path(first.manifest_path or "").is_file()
    assert second.is_clean and second.reused and not second.downloaded
    assert not tuple(destination.glob("*.part"))


def test_tampered_download_is_rejected_without_partial_file(tmp_path: Path) -> None:
    metadata_path, artifact, key = _metadata(tmp_path)
    check = check_for_application_update(
        metadata_path,
        "1.0.0",
        platform="windows",
        signing_key=key,
    )
    artifact.write_bytes(b"tampered")
    destination = tmp_path / "updates"
    result = stage_application_update(check, destination=destination)
    assert not result.is_clean
    assert not result.staged
    assert not (destination / artifact.name).exists()
    assert not tuple(destination.glob("*.part"))


def test_http_metadata_source_is_rejected() -> None:
    result = check_for_application_update(
        "http://updates.example.invalid/latest.json",
        "1.0.0",
        platform="windows",
    )
    assert not result.is_clean
    assert "HTTPS" in " ".join(result.errors)


def test_signature_can_be_required(tmp_path: Path) -> None:
    artifact = tmp_path / "FTBQuestMaker-2.0.0-Setup.exe"
    artifact.write_bytes(b"installer")
    metadata_path = tmp_path / "latest.json"
    write_update_metadata(
        create_update_metadata(
            "2.0.0", "stable", {"windows": artifact}, base_url=tmp_path.as_uri()
        ),
        metadata_path,
    )
    result = check_for_application_update(
        metadata_path,
        "1.0.0",
        platform="windows",
        require_signature=True,
    )
    assert not result.is_clean
    assert "signed update metadata is required" in result.errors

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    payload["artifacts"][0]["filename"] = r"..\escape.exe"
    payload["artifacts"][0]["url"] = r"..\escape.exe"
    metadata_path.write_text(json.dumps(payload), encoding="utf-8")
    unsafe = check_for_application_update(
        metadata_path,
        "1.0.0",
        platform="windows",
    )
    assert not unsafe.is_clean
    assert "unsafe update artifact filename" in " ".join(unsafe.errors)


def test_stable_client_rejects_beta_channel(tmp_path: Path) -> None:
    artifact = tmp_path / "FTBQuestMaker-2.0.0-beta.1-Setup.exe"
    artifact.write_bytes(b"installer")
    metadata_path = tmp_path / "latest.json"
    write_update_metadata(
        create_update_metadata(
            "2.0.0-beta.1",
            "beta",
            {"windows": artifact},
            base_url=tmp_path.as_uri(),
        ),
        metadata_path,
    )
    result = check_for_application_update(
        metadata_path,
        "1.0.0",
        channel="stable",
        platform="windows",
    )
    assert not result.is_clean
    assert "do not accept beta" in " ".join(result.errors)
