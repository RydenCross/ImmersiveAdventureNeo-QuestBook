from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile

from generator.application_updates import (
    check_for_application_update,
    compare_release_versions,
    stage_application_update,
)
from generator.desktop_packages import create_update_metadata, write_update_metadata


@dataclass(frozen=True, slots=True)
class ApplicationUpdatesContract:
    semantic_version_ordering: bool
    signed_update_detected: bool
    current_release_not_reoffered: bool
    staged_download_verified: bool
    staged_download_reused: bool
    tampered_download_rejected: bool
    insecure_metadata_rejected: bool
    channel_policy_enforced: bool

    @property
    def is_clean(self) -> bool:
        return all(
            (
                self.semantic_version_ordering,
                self.signed_update_detected,
                self.current_release_not_reoffered,
                self.staged_download_verified,
                self.staged_download_reused,
                self.tampered_download_rejected,
                self.insecure_metadata_rejected,
                self.channel_policy_enforced,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "semantic_version_ordering": self.semantic_version_ordering,
            "signed_update_detected": self.signed_update_detected,
            "current_release_not_reoffered": self.current_release_not_reoffered,
            "staged_download_verified": self.staged_download_verified,
            "staged_download_reused": self.staged_download_reused,
            "tampered_download_rejected": self.tampered_download_rejected,
            "insecure_metadata_rejected": self.insecure_metadata_rejected,
            "channel_policy_enforced": self.channel_policy_enforced,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Application update client contract: {'PASS' if self.is_clean else 'FAIL'}",
                f"Semantic version ordering: {'pass' if self.semantic_version_ordering else 'fail'}.",
                f"Signed update detection: {'pass' if self.signed_update_detected else 'fail'}.",
                f"Verified staging: {'pass' if self.staged_download_verified else 'fail'}.",
                f"Tamper rejection: {'pass' if self.tampered_download_rejected else 'fail'}.",
            )
        )


def run_application_updates_contract() -> ApplicationUpdatesContract:
    with tempfile.TemporaryDirectory(prefix="ftbq-application-updates-") as temporary:
        root = Path(temporary)
        artifact = root / "FTBQuestMaker-1.2.0-Setup.exe"
        artifact.write_bytes(b"verified-windows-installer")
        signing_key = b"application-update-contract-key"
        metadata = create_update_metadata(
            "1.2.0",
            "stable",
            {"windows": artifact},
            base_url=root.as_uri(),
            signing_key=signing_key,
            key_id="contract",
        )
        metadata_path = root / "latest.json"
        write_update_metadata(metadata, metadata_path)
        available = check_for_application_update(
            metadata_path,
            "1.1.0",
            platform="windows",
            signing_key=signing_key,
            require_signature=True,
        )
        current = check_for_application_update(
            metadata_path,
            "1.2.0",
            platform="windows",
            signing_key=signing_key,
            require_signature=True,
        )
        stage_directory = root / "staged"
        staged = stage_application_update(available, destination=stage_directory)
        reused = stage_application_update(available, destination=stage_directory)
        artifact.write_bytes(b"tampered")
        tampered = stage_application_update(available, destination=root / "tampered-stage")
        insecure = check_for_application_update(
            "http://updates.example.invalid/latest.json",
            "1.1.0",
            platform="windows",
        )
        beta_metadata = create_update_metadata(
            "1.3.0-beta.1",
            "beta",
            {"windows": artifact},
            base_url=root.as_uri(),
        )
        beta_path = root / "beta.json"
        write_update_metadata(beta_metadata, beta_path)
        stable_client = check_for_application_update(
            beta_path,
            "1.2.0",
            platform="windows",
            channel="stable",
        )
        return ApplicationUpdatesContract(
            semantic_version_ordering=(
                compare_release_versions("1.2.0", "1.2.0-beta.2") > 0
                and compare_release_versions("1.2.0-beta.10", "1.2.0-beta.2") > 0
                and compare_release_versions("1.2.1", "1.2.0") > 0
            ),
            signed_update_detected=(
                available.is_clean
                and available.update_available
                and available.metadata_signed
                and available.signature_valid is True
            ),
            current_release_not_reoffered=(current.is_clean and not current.update_available),
            staged_download_verified=(
                staged.is_clean
                and staged.downloaded
                and staged.staged
                and Path(staged.manifest_path or "").is_file()
            ),
            staged_download_reused=(reused.is_clean and reused.reused and not reused.downloaded),
            tampered_download_rejected=(
                not tampered.is_clean
                and not tampered.staged
                and any(label in " ".join(tampered.errors) for label in ("SHA-256", "size"))
            ),
            insecure_metadata_rejected=(
                not insecure.is_clean and "HTTPS" in " ".join(insecure.errors)
            ),
            channel_policy_enforced=(
                not stable_client.is_clean
                and "do not accept beta" in " ".join(stable_client.errors)
            ),
        )
