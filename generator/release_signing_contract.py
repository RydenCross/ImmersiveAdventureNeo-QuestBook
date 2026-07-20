from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import tempfile

from generator.release_signing import (
    create_attestation_verification_plan,
    create_checksum_manifest,
    verify_checksum_manifest,
    verify_github_attestations,
    write_checksum_manifest,
)


@dataclass(frozen=True, slots=True)
class ReleaseSigningContract:
    deterministic_checksums: bool
    checksum_verification: bool
    tampering_detected: bool
    atomic_write_verified: bool
    deterministic_verification_plan: bool
    dry_run_safe: bool
    execution_failure_detected: bool
    unsafe_inputs_rejected: bool
    workflow_integrated: bool

    @property
    def is_clean(self) -> bool:
        return all(getattr(self, field) for field in self.__dataclass_fields__)

    def to_dict(self) -> dict[str, object]:
        return {"status": "pass" if self.is_clean else "fail", **{field: getattr(self, field) for field in self.__dataclass_fields__}}

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return f"Keyless release signing and verification contract: {'PASS' if self.is_clean else 'FAIL'}"


def run_release_signing_contract() -> ReleaseSigningContract:
    with tempfile.TemporaryDirectory(prefix="ftbq-signing-") as temporary:
        root = Path(temporary)
        windows = root / "FTB-Quest-Maker.exe"
        linux = root / "FTB-Quest-Maker.AppImage"
        windows.write_bytes(b"windows")
        linux.write_bytes(b"linux")
        artifacts = [windows, linux]
        first = create_checksum_manifest(artifacts)
        second = create_checksum_manifest(list(reversed(artifacts)))
        manifest = write_checksum_manifest(root / "nested" / "SHA256SUMS", artifacts)
        before = verify_checksum_manifest(manifest, root)
        windows.write_bytes(b"tampered")
        after = verify_checksum_manifest(manifest, root)
        windows.write_bytes(b"windows")
        plan = create_attestation_verification_plan(artifacts, repository="owner/project")
        plan_again = create_attestation_verification_plan(list(reversed(artifacts)), repository="owner/project")
        calls: list[tuple[str, ...]] = []

        def success(command: tuple[str, ...], **_: object) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, "verified", "")

        verify_github_attestations(artifacts, repository="owner/project", execute=False, runner=success)
        dry_run_safe = not calls
        failed = False
        try:
            verify_github_attestations(
                [windows],
                repository="owner/project",
                execute=True,
                runner=lambda command, **_: subprocess.CompletedProcess(command, 1, "", "bad signature"),
            )
        except RuntimeError:
            failed = True
        rejected = False
        try:
            create_attestation_verification_plan([windows], repository="https://github.com/owner/project")
        except ValueError:
            rejected = True
        workflow = Path(".github/workflows/publish-release.yml").read_text(encoding="utf-8")
        return ReleaseSigningContract(
            deterministic_checksums=first == second,
            checksum_verification=not before,
            tampering_detected=bool(after),
            atomic_write_verified=manifest.is_file() and not manifest.with_name(manifest.name + ".tmp").exists(),
            deterministic_verification_plan=plan == plan_again,
            dry_run_safe=dry_run_safe,
            execution_failure_detected=failed,
            unsafe_inputs_rejected=rejected,
            workflow_integrated=("actions/attest@v4" in workflow and "attestations: write" in workflow and "SHA256SUMS" in workflow),
        )
