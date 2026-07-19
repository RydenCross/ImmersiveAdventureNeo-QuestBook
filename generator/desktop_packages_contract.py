from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from generator.desktop_packages import (
    build_desktop_package,
    create_desktop_package_plan,
    create_update_metadata,
    verify_update_metadata,
    write_update_metadata,
)


@dataclass(frozen=True, slots=True)
class DesktopPackagesContract:
    deterministic_package_plans: bool
    platform_artifact_names: bool
    dry_run_supported: bool
    cross_build_rejected: bool
    linux_appdir_staged: bool
    deterministic_update_metadata: bool
    signed_metadata_verified: bool
    tampered_artifact_rejected: bool
    wrong_signing_key_rejected: bool
    packaging_recipes_present: bool

    @property
    def is_clean(self) -> bool:
        return all(
            (
                self.deterministic_package_plans,
                self.platform_artifact_names,
                self.dry_run_supported,
                self.cross_build_rejected,
                self.linux_appdir_staged,
                self.deterministic_update_metadata,
                self.signed_metadata_verified,
                self.tampered_artifact_rejected,
                self.wrong_signing_key_rejected,
                self.packaging_recipes_present,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "deterministic_package_plans": self.deterministic_package_plans,
            "platform_artifact_names": self.platform_artifact_names,
            "dry_run_supported": self.dry_run_supported,
            "cross_build_rejected": self.cross_build_rejected,
            "linux_appdir_staged": self.linux_appdir_staged,
            "deterministic_update_metadata": self.deterministic_update_metadata,
            "signed_metadata_verified": self.signed_metadata_verified,
            "tampered_artifact_rejected": self.tampered_artifact_rejected,
            "wrong_signing_key_rejected": self.wrong_signing_key_rejected,
            "packaging_recipes_present": self.packaging_recipes_present,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        checks = (
            ("Deterministic package plans", self.deterministic_package_plans),
            ("Platform artifact names", self.platform_artifact_names),
            ("Dry-run package builds", self.dry_run_supported),
            ("Cross-build rejection", self.cross_build_rejected),
            ("Linux AppDir staging", self.linux_appdir_staged),
            ("Deterministic update metadata", self.deterministic_update_metadata),
            ("Signed metadata verification", self.signed_metadata_verified),
            ("Tampered artifact rejection", self.tampered_artifact_rejected),
            ("Wrong signing-key rejection", self.wrong_signing_key_rejected),
            ("Packaging recipes", self.packaging_recipes_present),
        )
        lines = [
            f"Desktop installers and update metadata contract: "
            f"{'PASS' if self.is_clean else 'FAIL'}"
        ]
        lines.extend(f"{name}: {'PASS' if passed else 'FAIL'}." for name, passed in checks)
        return "\n".join(lines)


def run_desktop_packages_contract() -> DesktopPackagesContract:
    with TemporaryDirectory(prefix="desktop-packages-contract-") as temporary:
        root = Path(temporary)
        native = root / "native"
        packages = root / "packages"
        native.mkdir()
        (native / "FTBQuestMaker").write_bytes(b"linux-native-binary")
        (native / "FTBQuestMaker.exe").write_bytes(b"windows-native-binary")

        windows_first = create_desktop_package_plan(
            "windows", "1.2.3", native_directory=native, destination=packages
        )
        windows_second = create_desktop_package_plan(
            "windows", "1.2.3", native_directory=native, destination=packages
        )
        linux = create_desktop_package_plan(
            "linux", "1.2.3", native_directory=native, destination=packages
        )
        dry_run = build_desktop_package(
            "windows",
            "1.2.3",
            native_directory=native,
            destination=packages,
            dry_run=True,
            system_name="Windows",
        )
        cross_build = build_desktop_package(
            "windows",
            "1.2.3",
            native_directory=native,
            destination=packages,
            system_name="Linux",
            tool_available=True,
        )

        def fake_appimage_runner(
            command: tuple[str, ...], **_kwargs: object
        ) -> subprocess.CompletedProcess[object]:
            Path(command[-1]).write_bytes(b"deterministic-appimage")
            return subprocess.CompletedProcess(command, 0)

        linux_build = build_desktop_package(
            "linux",
            "1.2.3",
            native_directory=native,
            destination=packages,
            system_name="Linux",
            tool="appimagetool-contract",
            tool_available=True,
            runner=fake_appimage_runner,
        )
        appdir = Path(linux.build_directory or "")

        windows_artifact = packages / "FTBQuestMaker-1.2.3-Setup.exe"
        windows_artifact.write_bytes(b"windows-installer")
        linux_artifact = Path(linux.artifact_path)
        key = b"contract-signing-key"
        artifacts = {"windows": windows_artifact, "linux": linux_artifact}
        first_metadata = create_update_metadata(
            "1.2.3",
            "stable",
            artifacts,
            base_url="https://updates.example.invalid",
            signing_key=key,
        )
        second_metadata = create_update_metadata(
            "1.2.3",
            "stable",
            artifacts,
            base_url="https://updates.example.invalid",
            signing_key=key,
        )
        metadata_path = root / "updates/latest.json"
        write_update_metadata(first_metadata, metadata_path)
        verified = verify_update_metadata(
            metadata_path, artifact_directory=packages, signing_key=key
        )
        wrong_key = verify_update_metadata(
            metadata_path, artifact_directory=packages, signing_key=b"wrong-key"
        )
        linux_artifact.write_bytes(b"tampered-appimage")
        tampered = verify_update_metadata(
            metadata_path, artifact_directory=packages, signing_key=key
        )

        recipes = (
            Path("packaging/windows/ftb_quest_maker.iss"),
            Path("packaging/windows/build_installer.ps1"),
            Path("packaging/linux/AppRun"),
            Path("packaging/linux/build_appimage.sh"),
            Path("packaging/linux/ftb-quest-maker.svg"),
        )
        return DesktopPackagesContract(
            deterministic_package_plans=windows_first.to_dict() == windows_second.to_dict(),
            platform_artifact_names=(
                windows_first.artifact_path.endswith("FTBQuestMaker-1.2.3-Setup.exe")
                and linux.artifact_path.endswith("FTBQuestMaker-1.2.3-x86_64.AppImage")
            ),
            dry_run_supported=dry_run.is_clean and dry_run.dry_run and not dry_run.built,
            cross_build_rejected=(
                not cross_build.is_clean
                and cross_build.return_code == 2
                and "target operating system" in cross_build.errors[0]
            ),
            linux_appdir_staged=(
                linux_build.is_clean
                and (appdir / "AppRun").is_file()
                and (appdir / "usr/bin/FTBQuestMaker").is_file()
                and (appdir / "ftb-quest-maker.desktop").is_file()
                and (appdir / "ftb-quest-maker.svg").is_file()
            ),
            deterministic_update_metadata=(
                first_metadata.format_json() == second_metadata.format_json()
            ),
            signed_metadata_verified=(
                verified.is_clean
                and verified.metadata_signed
                and verified.signature_valid is True
                and len(verified.verified_artifacts) == 2
            ),
            tampered_artifact_rejected=(
                not tampered.is_clean
                and linux_artifact.name in tampered.changed_artifacts
            ),
            wrong_signing_key_rejected=(
                not wrong_key.is_clean
                and wrong_key.signature_valid is False
                and "signature mismatch" in " ".join(wrong_key.errors)
            ),
            packaging_recipes_present=all(path.is_file() for path in recipes),
        )
