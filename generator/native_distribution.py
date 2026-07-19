from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import platform as platform_module
import subprocess
import sys
from typing import Callable, Sequence

SUPPORTED_NATIVE_PLATFORMS = ("windows", "linux")
DEFAULT_DISTRIBUTION_DIRECTORY = Path("dist/native")
DEFAULT_SPEC_PATH = Path("packaging/ftb_quest_maker.spec")


def detect_native_platform(system_name: str | None = None) -> str:
    selected = (system_name or platform_module.system()).strip().casefold()
    if selected.startswith("win"):
        return "windows"
    if selected == "linux":
        return "linux"
    selected_name = system_name or platform_module.system()
    raise ValueError(f"unsupported native desktop platform: {selected_name}")


@dataclass(frozen=True, slots=True)
class NativeDistributionPlan:
    platform: str
    application_name: str
    executable_name: str
    destination: str
    spec_path: str
    command: tuple[str, ...]
    first_run_preferences: str
    build_on_target_required: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "platform": self.platform,
            "application_name": self.application_name,
            "executable_name": self.executable_name,
            "destination": self.destination,
            "spec_path": self.spec_path,
            "command": list(self.command),
            "first_run_preferences": self.first_run_preferences,
            "build_on_target_required": self.build_on_target_required,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            "Native desktop distribution plan: PASS",
            f"Platform: {self.platform}.",
            f"Executable: {self.executable_name}.",
            f"Destination: {self.destination}.",
            f"Spec: {self.spec_path}.",
            "Command: " + " ".join(self.command),
        ))


@dataclass(frozen=True, slots=True)
class NativeBuildResult:
    plan: NativeDistributionPlan
    dry_run: bool
    built: bool
    return_code: int
    errors: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not self.errors and (self.dry_run or self.built)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "dry_run": self.dry_run,
            "built": self.built,
            "return_code": self.return_code,
            "errors": list(self.errors),
            "plan": self.plan.to_dict(),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Native desktop build: {'PASS' if self.is_clean else 'FAIL'}",
            f"Platform: {self.plan.platform}.",
            f"Dry run: {'yes' if self.dry_run else 'no'}.",
            f"Built: {'yes' if self.built else 'no'}.",
            f"Return code: {self.return_code}.",
        ]
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


def create_native_distribution_plan(
    platform: str = "auto",
    *,
    destination: Path = DEFAULT_DISTRIBUTION_DIRECTORY,
    spec_path: Path = DEFAULT_SPEC_PATH,
    python_executable: str | None = None,
    system_name: str | None = None,
) -> NativeDistributionPlan:
    selected = detect_native_platform(system_name) if platform == "auto" else platform.casefold()
    if selected not in SUPPORTED_NATIVE_PLATFORMS:
        raise ValueError(f"platform must be one of: {', '.join(SUPPORTED_NATIVE_PLATFORMS)}")
    executable = "FTBQuestMaker.exe" if selected == "windows" else "FTBQuestMaker"
    destination = Path(destination)
    spec_path = Path(spec_path)
    command = (
        python_executable or sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        destination.as_posix(),
        spec_path.as_posix(),
    )
    return NativeDistributionPlan(
        platform=selected,
        application_name="FTB Quest Maker",
        executable_name=executable,
        destination=destination.as_posix(),
        spec_path=spec_path.as_posix(),
        command=command,
        first_run_preferences="~/.ftb-quest-maker/preferences.json",
    )


def build_native_distribution(
    platform: str = "auto",
    *,
    destination: Path = DEFAULT_DISTRIBUTION_DIRECTORY,
    spec_path: Path = DEFAULT_SPEC_PATH,
    dry_run: bool = False,
    system_name: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[object]] = subprocess.run,
    pyinstaller_available: bool | None = None,
) -> NativeBuildResult:
    plan = create_native_distribution_plan(
        platform,
        destination=destination,
        spec_path=spec_path,
        system_name=system_name,
    )
    host = detect_native_platform(system_name)
    if not dry_run and plan.platform != host:
        return NativeBuildResult(
            plan,
            dry_run=False,
            built=False,
            return_code=2,
            errors=("native distributions must be built on the target operating system",),
        )
    if not Path(plan.spec_path).is_file():
        return NativeBuildResult(
            plan,
            dry_run=dry_run,
            built=False,
            return_code=2,
            errors=(f"missing PyInstaller spec: {plan.spec_path}",),
        )
    if dry_run:
        return NativeBuildResult(plan, dry_run=True, built=False, return_code=0)
    available = (
        importlib.util.find_spec("PyInstaller") is not None
        if pyinstaller_available is None
        else pyinstaller_available
    )
    if not available:
        return NativeBuildResult(
            plan,
            dry_run=False,
            built=False,
            return_code=2,
            errors=("PyInstaller is not installed; install the desktop optional dependency",),
        )
    Path(plan.destination).mkdir(parents=True, exist_ok=True)
    completed = runner(plan.command, check=False)
    return NativeBuildResult(
        plan,
        dry_run=False,
        built=completed.returncode == 0,
        return_code=int(completed.returncode),
        errors=() if completed.returncode == 0 else ("PyInstaller build failed",),
    )
