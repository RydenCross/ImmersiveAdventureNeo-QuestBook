from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from generator.desktop_setup import (
    complete_first_run_setup,
    load_desktop_preferences,
    update_last_instance,
)
from generator.native_distribution import (
    build_native_distribution,
    create_native_distribution_plan,
)


@dataclass(frozen=True, slots=True)
class NativeDistributionContract:
    first_run_setup: bool
    preferences_round_trip: bool
    corrupt_preferences_recovered: bool
    deterministic_build_plan: bool
    platform_specific_executables: bool
    dry_run_supported: bool
    cross_build_rejected: bool
    packaged_entrypoint: bool
    build_recipes_present: bool
    launcher_preferences_integrated: bool

    @property
    def is_clean(self) -> bool:
        return all((
            self.first_run_setup,
            self.preferences_round_trip,
            self.corrupt_preferences_recovered,
            self.deterministic_build_plan,
            self.platform_specific_executables,
            self.dry_run_supported,
            self.cross_build_rejected,
            self.packaged_entrypoint,
            self.build_recipes_present,
            self.launcher_preferences_integrated,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "first_run_setup": self.first_run_setup,
            "preferences_round_trip": self.preferences_round_trip,
            "corrupt_preferences_recovered": self.corrupt_preferences_recovered,
            "deterministic_build_plan": self.deterministic_build_plan,
            "platform_specific_executables": self.platform_specific_executables,
            "dry_run_supported": self.dry_run_supported,
            "cross_build_rejected": self.cross_build_rejected,
            "packaged_entrypoint": self.packaged_entrypoint,
            "build_recipes_present": self.build_recipes_present,
            "launcher_preferences_integrated": self.launcher_preferences_integrated,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        values = (
            ("First-run setup", self.first_run_setup),
            ("Preferences round trip", self.preferences_round_trip),
            ("Corrupt preferences recovery", self.corrupt_preferences_recovered),
            ("Deterministic build plan", self.deterministic_build_plan),
            ("Platform-specific executables", self.platform_specific_executables),
            ("Dry-run build", self.dry_run_supported),
            ("Cross-build rejection", self.cross_build_rejected),
            ("Packaged entrypoint", self.packaged_entrypoint),
            ("Build recipes", self.build_recipes_present),
            ("Launcher preferences integration", self.launcher_preferences_integrated),
        )
        lines = [
            f"Native desktop distribution contract: {'PASS' if self.is_clean else 'FAIL'}"
        ]
        lines.extend(f"{name}: {'PASS' if passed else 'FAIL'}." for name, passed in values)
        return "\n".join(lines)


def run_native_distribution_contract() -> NativeDistributionContract:
    with TemporaryDirectory(prefix="native-distribution-contract-") as temporary:
        root = Path(temporary)
        preferences_path = root / "preferences.json"
        workspace = root / "workspace"
        custom_root = root / "instances"
        custom_root.mkdir()
        setup = complete_first_run_setup(
            preferences_path=preferences_path,
            workspace_root=workspace,
            search_roots=(custom_root,),
            open_browser=False,
            max_instances=125,
        )
        loaded = load_desktop_preferences(preferences_path)
        updated = update_last_instance(
            loaded.preferences,
            "instance-contract",
            path=preferences_path,
        )
        reloaded = load_desktop_preferences(preferences_path)

        corrupt = root / "corrupt.json"
        corrupt.write_text("{not valid json", encoding="utf-8")
        recovered = load_desktop_preferences(corrupt)

        windows_first = create_native_distribution_plan(
            "windows",
            destination=root / "dist",
            python_executable="python-contract",
        )
        windows_second = create_native_distribution_plan(
            "windows",
            destination=root / "dist",
            python_executable="python-contract",
        )
        linux = create_native_distribution_plan(
            "linux",
            destination=root / "dist",
            python_executable="python-contract",
        )
        dry_run = build_native_distribution(
            "linux",
            destination=root / "dist",
            dry_run=True,
            system_name="Linux",
        )
        cross_build = build_native_distribution(
            "windows",
            destination=root / "dist",
            dry_run=False,
            system_name="Linux",
            pyinstaller_available=True,
            runner=lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0),
        )

        entrypoint = Path("generator/desktop_entry.py")
        spec = Path("packaging/ftb_quest_maker.spec")
        windows_script = Path("packaging/build_windows.ps1")
        linux_script = Path("packaging/build_linux.sh")
        desktop_file = Path("packaging/ftb-quest-maker.desktop")
        launcher_source = Path("generator/desktop_launcher.py").read_text(encoding="utf-8")

        return NativeDistributionContract(
            first_run_setup=(
                setup.is_clean
                and preferences_path.is_file()
                and (workspace / "workspaces").is_dir()
                and (workspace / "logs").is_dir()
            ),
            preferences_round_trip=(
                loaded.is_clean
                and loaded.preferences.search_roots == (custom_root.as_posix(),)
                and not loaded.preferences.open_browser
                and loaded.preferences.max_instances == 125
                and updated.last_instance_id == "instance-contract"
                and reloaded.preferences.last_instance_id == "instance-contract"
            ),
            corrupt_preferences_recovered=(
                recovered.source == "recovered"
                and bool(recovered.warnings)
                and not recovered.preferences.first_run_complete
            ),
            deterministic_build_plan=windows_first.to_dict() == windows_second.to_dict(),
            platform_specific_executables=(
                windows_first.executable_name == "FTBQuestMaker.exe"
                and linux.executable_name == "FTBQuestMaker"
                and windows_first.build_on_target_required
                and linux.build_on_target_required
            ),
            dry_run_supported=dry_run.is_clean and dry_run.dry_run and not dry_run.built,
            cross_build_rejected=(
                not cross_build.is_clean
                and cross_build.return_code == 2
                and "target operating system" in cross_build.errors[0]
            ),
            packaged_entrypoint=(
                entrypoint.is_file()
                and "launch_desktop" in entrypoint.read_text(encoding="utf-8")
                and spec.is_file()
                and "generator/desktop_entry.py" in spec.read_text(encoding="utf-8")
                and "console=False" in spec.read_text(encoding="utf-8")
            ),
            build_recipes_present=(
                windows_script.is_file()
                and linux_script.is_file()
                and desktop_file.is_file()
                and "quest-maker-native-build --platform windows"
                in windows_script.read_text(encoding="utf-8")
                and "quest-maker-native-build --platform linux"
                in linux_script.read_text(encoding="utf-8")
            ),
            launcher_preferences_integrated=all(
                token in launcher_source
                for token in (
                    "load_desktop_preferences",
                    "preferences_dialog",
                    "first_run_complete",
                    "Preferences…",
                    "update_last_instance",
                )
            ),
        )
