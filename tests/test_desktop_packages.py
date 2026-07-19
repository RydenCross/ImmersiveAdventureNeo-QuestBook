from pathlib import Path
import subprocess

import pytest

from generator.desktop_packages import (
    build_desktop_package,
    create_desktop_package_plan,
    create_update_metadata,
    parse_artifact_specs,
    validate_release_version,
    verify_update_metadata,
    write_update_metadata,
)


def test_package_plans_use_platform_specific_artifact_names(tmp_path: Path) -> None:
    windows = create_desktop_package_plan(
        "windows", "2.4.0", native_directory=tmp_path / "native", destination=tmp_path
    )
    linux = create_desktop_package_plan(
        "linux", "2.4.0", native_directory=tmp_path / "native", destination=tmp_path
    )
    assert windows.artifact_path.endswith("FTBQuestMaker-2.4.0-Setup.exe")
    assert windows.tool == "iscc"
    assert linux.artifact_path.endswith("FTBQuestMaker-2.4.0-x86_64.AppImage")
    assert linux.tool == "appimagetool"


def test_invalid_release_versions_are_rejected() -> None:
    with pytest.raises(ValueError, match="semantic version"):
        validate_release_version("release-candidate")


def test_linux_package_build_stages_appdir_and_hashes_artifact(tmp_path: Path) -> None:
    native = tmp_path / "native"
    native.mkdir()
    (native / "FTBQuestMaker").write_bytes(b"native-binary")

    def runner(
        command: tuple[str, ...], **_kwargs: object
    ) -> subprocess.CompletedProcess[object]:
        Path(command[-1]).write_bytes(b"appimage")
        return subprocess.CompletedProcess(command, 0)

    result = build_desktop_package(
        "linux",
        "1.0.0",
        native_directory=native,
        destination=tmp_path / "packages",
        system_name="Linux",
        tool="appimagetool-test",
        tool_available=True,
        runner=runner,
    )
    appdir = Path(result.plan.build_directory or "")
    assert result.is_clean
    assert result.built
    assert result.artifact_bytes == len(b"appimage")
    assert (appdir / "AppRun").is_file()
    assert (appdir / "usr/bin/FTBQuestMaker").is_file()


def test_cross_platform_package_build_is_rejected(tmp_path: Path) -> None:
    result = build_desktop_package(
        "windows",
        "1.0.0",
        native_directory=tmp_path,
        destination=tmp_path / "packages",
        system_name="Linux",
        tool_available=True,
    )
    assert not result.is_clean
    assert "target operating system" in result.errors[0]


def test_signed_update_metadata_round_trips_and_detects_tampering(tmp_path: Path) -> None:
    windows = tmp_path / "FTBQuestMaker-1.0.0-Setup.exe"
    linux = tmp_path / "FTBQuestMaker-1.0.0-x86_64.AppImage"
    windows.write_bytes(b"windows")
    linux.write_bytes(b"linux")
    key = b"release-signing-key"
    metadata = create_update_metadata(
        "1.0.0",
        "stable",
        {"windows": windows, "linux": linux},
        base_url="https://updates.example.invalid/releases",
        signing_key=key,
        key_id="test-key",
    )
    destination = tmp_path / "latest.json"
    build = write_update_metadata(metadata, destination)
    verified = verify_update_metadata(
        destination, artifact_directory=tmp_path, signing_key=key
    )
    assert build.is_clean
    assert build.signed
    assert verified.is_clean
    assert verified.signature_valid is True
    assert len(verified.verified_artifacts) == 2

    linux.write_bytes(b"changed")
    changed = verify_update_metadata(
        destination, artifact_directory=tmp_path, signing_key=key
    )
    assert not changed.is_clean
    assert linux.name in changed.changed_artifacts


def test_wrong_update_signing_key_is_rejected(tmp_path: Path) -> None:
    artifact = tmp_path / "FTBQuestMaker-1.0.0-Setup.exe"
    artifact.write_bytes(b"windows")
    destination = tmp_path / "latest.json"
    metadata = create_update_metadata(
        "1.0.0", "stable", {"windows": artifact}, signing_key=b"right"
    )
    write_update_metadata(metadata, destination)
    result = verify_update_metadata(destination, signing_key=b"wrong")
    assert not result.is_clean
    assert result.signature_valid is False


def test_artifact_specs_support_explicit_and_inferred_platforms(tmp_path: Path) -> None:
    windows = tmp_path / "setup.exe"
    linux = tmp_path / "app.AppImage"
    parsed = parse_artifact_specs((f"windows={windows}", str(linux)))
    assert parsed == {"windows": windows, "linux": linux}


def test_stable_channel_rejects_prerelease_versions(tmp_path: Path) -> None:
    artifact = tmp_path / "FTBQuestMaker-1.0.0-beta.1-Setup.exe"
    artifact.write_bytes(b"windows")
    with pytest.raises(ValueError, match="stable"):
        create_update_metadata(
            "1.0.0-beta.1", "stable", {"windows": artifact}
        )
