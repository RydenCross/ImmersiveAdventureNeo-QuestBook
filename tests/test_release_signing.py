from pathlib import Path
import subprocess

import pytest

from generator.release_signing import (
    create_attestation_verification_plan,
    create_checksum_manifest,
    verify_checksum_manifest,
    verify_github_attestations,
    write_checksum_manifest,
)


def test_checksum_manifest_is_deterministic_and_detects_tampering(tmp_path: Path) -> None:
    a = tmp_path / "a.exe"; b = tmp_path / "b.AppImage"
    a.write_bytes(b"a"); b.write_bytes(b"b")
    assert create_checksum_manifest([a, b]) == create_checksum_manifest([b, a])
    manifest = write_checksum_manifest(tmp_path / "SHA256SUMS", [a, b])
    assert verify_checksum_manifest(manifest, tmp_path) == ()
    a.write_bytes(b"changed")
    assert verify_checksum_manifest(manifest, tmp_path) == ("checksum mismatch: a.exe",)


def test_attestation_verification_is_safe_by_default(tmp_path: Path) -> None:
    artifact = tmp_path / "app.zip"; artifact.write_bytes(b"ok")
    plan = create_attestation_verification_plan([artifact], repository="owner/repo")
    assert plan.commands[0][:3] == ("gh", "attestation", "verify")
    called = False
    def runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        nonlocal called; called = True
        return subprocess.CompletedProcess(args, 0, "", "")
    verify_github_attestations([artifact], repository="owner/repo", runner=runner)
    assert not called
    with pytest.raises(ValueError):
        create_attestation_verification_plan([artifact], repository="bad repository")
