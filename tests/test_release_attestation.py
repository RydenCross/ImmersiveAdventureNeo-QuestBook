from pathlib import Path

import pytest

from generator.release_attestation import create_cyclonedx_sbom, create_slsa_provenance, verify_attestation_subjects


def test_sbom_and_provenance_are_deterministic(tmp_path: Path) -> None:
    a = tmp_path / "a.zip"; b = tmp_path / "b.AppImage"
    a.write_bytes(b"a"); b.write_bytes(b"b")
    assert create_cyclonedx_sbom([a, b], version="1.0.0") == create_cyclonedx_sbom([b, a], version="1.0.0")
    first = create_slsa_provenance([a, b], repository="https://github.com/o/r", revision="abc", workflow=".github/workflows/publish-release.yml")
    second = create_slsa_provenance([b, a], repository="https://github.com/o/r", revision="abc", workflow=".github/workflows/publish-release.yml")
    assert first == second
    assert verify_attestation_subjects(first, [a, b]) == ()


def test_provenance_detects_tampering_and_rejects_unsafe_inputs(tmp_path: Path) -> None:
    artifact = tmp_path / "app.zip"; artifact.write_bytes(b"ok")
    provenance = create_slsa_provenance([artifact], repository="https://github.com/o/r", revision="abc", workflow=".github/workflows/publish-release.yml")
    artifact.write_bytes(b"changed")
    assert verify_attestation_subjects(provenance, [artifact])
    with pytest.raises(ValueError):
        create_slsa_provenance([artifact], repository="http://github.com/o/r", revision="bad ref", workflow="publish.yml")
