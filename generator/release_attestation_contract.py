from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile

from generator.release_attestation import (
    create_cyclonedx_sbom,
    create_slsa_provenance,
    verify_attestation_subjects,
    write_json_document,
)


@dataclass(frozen=True, slots=True)
class ReleaseAttestationContract:
    deterministic_sbom: bool
    deterministic_provenance: bool
    artifact_digests_verified: bool
    tampering_detected: bool
    atomic_writes_verified: bool
    unsafe_inputs_rejected: bool
    workflow_integrated: bool
    verified_source_revision_bound: bool
    release_version_bound: bool

    @property
    def is_clean(self) -> bool:
        return all(getattr(self, name) for name in self.__dataclass_fields__)

    def to_dict(self) -> dict[str, object]:
        return {"status": "pass" if self.is_clean else "fail", **{name: getattr(self, name) for name in self.__dataclass_fields__}}

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return f"Release SBOM and provenance contract: {'PASS' if self.is_clean else 'FAIL'}"


def run_release_attestation_contract() -> ReleaseAttestationContract:
    with tempfile.TemporaryDirectory(prefix="ftbq-attestation-") as temporary:
        root = Path(temporary)
        first = root / "FTB-Quest-Maker.exe"
        second = root / "FTB-Quest-Maker.AppImage"
        first.write_bytes(b"windows")
        second.write_bytes(b"linux")
        artifacts = [second, first]
        sbom = create_cyclonedx_sbom(artifacts, version="1.2.3", components=[("pytest", "8.0.0"), ("black", "24.0.0")])
        sbom_again = create_cyclonedx_sbom(list(reversed(artifacts)), version="1.2.3", components=[("black", "24.0.0"), ("pytest", "8.0.0")])
        provenance = create_slsa_provenance(artifacts, repository="https://github.com/owner/project", revision="abc123", workflow=".github/workflows/publish-release.yml")
        provenance_again = create_slsa_provenance(list(reversed(artifacts)), repository="https://github.com/owner/project", revision="abc123", workflow=".github/workflows/publish-release.yml")
        before = verify_attestation_subjects(provenance, artifacts)
        first.write_bytes(b"tampered")
        after = verify_attestation_subjects(provenance, artifacts)
        output = write_json_document(root / "nested" / "provenance.json", provenance)
        rejected = False
        try:
            create_slsa_provenance([second], repository="http://github.com/owner/project", revision="bad ref", workflow="publish.yml")
        except ValueError:
            rejected = True
        workflow = Path(".github/workflows/publish-release.yml").read_text(encoding="utf-8")
        return ReleaseAttestationContract(
            deterministic_sbom=sbom == sbom_again,
            deterministic_provenance=provenance == provenance_again,
            artifact_digests_verified=not before,
            tampering_detected=bool(after),
            atomic_writes_verified=output.is_file() and json.loads(output.read_text(encoding="utf-8")) == provenance and not output.with_name(output.name + ".tmp").exists(),
            unsafe_inputs_rejected=rejected,
            workflow_integrated="quest-maker-release-sbom" in workflow and "quest-maker-release-provenance" in workflow,
            verified_source_revision_bound=(
                'RELEASE_SOURCE_SHA="$(git rev-parse HEAD)"' in workflow
                and "printf '%s\\n' \"RELEASE_SOURCE_SHA=$RELEASE_SOURCE_SHA\" >> \"$GITHUB_ENV\"" in workflow
                and '--revision "$RELEASE_SOURCE_SHA"' in workflow
                and '${{ github.sha }}' not in workflow
            ),
            release_version_bound=(
                'RELEASE_VERSION="${{ inputs.tag }}"' in workflow
                and 'RELEASE_VERSION="${RELEASE_VERSION#v}"' in workflow
                and '"RELEASE_VERSION=$RELEASE_VERSION"' in workflow
                and '--version "$RELEASE_VERSION"' in workflow
                and '--expected-version "$RELEASE_VERSION"' in workflow
                and '--version "${{ inputs.tag }}"' not in workflow
            ),
        )
